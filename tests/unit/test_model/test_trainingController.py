"""Training HTTP controller contract tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from tinyShards import writeTinyShard

from apps.modules.model.controllers.trainingController import trainingBlueprint
from controllerTestFixtures import AUTH_HEADERS, TrainingContext, errorCode


@pytest.fixture
def training(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TrainingContext:
    """Training controller wired to temporary repositories."""
    return TrainingContext(tmp_path, monkeypatch)


@pytest.fixture
def deferredTraining(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TrainingContext:
    """Training controller whose worker pool never runs the job."""
    return TrainingContext(tmp_path, monkeypatch, inline=False)


class TestTrainingControllerWiring:
    """Blueprint metadata and authentication."""

    def test_blueprint_metadata(self) -> None:
        assert trainingBlueprint.name == "training"
        assert trainingBlueprint.url_prefix == "/api/training"

    @pytest.mark.parametrize(
        ("method", "path"),
        [
            ("get", "/api/training/jobs"),
            ("get", "/api/training/jobs/unknown"),
            ("get", "/api/training/checkpoints"),
            ("get", "/api/training/checkpoints/unknown"),
            ("get", "/api/training/presets"),
            ("post", "/api/training/jobs"),
            ("post", "/api/training/jobs/unknown/cancel"),
            ("post", "/api/training/jobs/unknown/resume"),
            ("get", "/api/training/jobs/unknown/stream"),
            ("get", "/api/training/jobs/unknown/history"),
            ("post", "/api/training/jobs/unknown/evaluate"),
        ],
    )
    def test_endpoints_require_auth(
        self, training: TrainingContext, method: str, path: str
    ) -> None:
        response = getattr(training.client, method)(path)

        assert response.status_code == 401
        assert errorCode(response) == "UNAUTHORIZED"

    def test_presets_lists_architectures(self, training: TrainingContext) -> None:
        response = training.client.get("/api/training/presets", headers=AUTH_HEADERS)

        assert response.status_code == 200
        payload = response.get_json()
        names = [entry["name"] for entry in payload]
        assert "tiny" in names
        tinyPreset = next(entry for entry in payload if entry["name"] == "tiny")
        assert tinyPreset["modelConfig"]["dim"] == 64
        assert tinyPreset["parameters"] > 0


class TestTrainingControllerStart:
    """Launching training jobs over HTTP."""

    def test_start_returns_202_and_completed_job(self, training: TrainingContext) -> None:
        response = training.start()

        assert response.status_code == 202
        payload = response.get_json()
        assert payload["jobType"] == "training"
        assert payload["status"] == "completed"
        assert payload["result"]["steps"] == 1
        assert payload["progress"]["step"] == 1
        assert payload["userId"] == "dev-user"

    def test_start_rejects_unknown_preset(self, training: TrainingContext) -> None:
        response = training.start(preset="galactic")

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"

    def test_start_rejects_seq_len_above_context(self, training: TrainingContext) -> None:
        response = training.start(seqLen=4096)

        assert response.status_code == 400
        error = response.get_json()["error"]
        assert error["code"] == "VALIDATION_ERROR"
        assert "seqLen" in error["message"]

    def test_start_rejects_invalid_hyper_parameter(self, training: TrainingContext) -> None:
        response = training.start(batchSize=0)

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"

    def test_start_requires_json_content_type(self, training: TrainingContext) -> None:
        response = training.client.post(
            "/api/training/jobs",
            headers=AUTH_HEADERS,
            data="preset=tiny",
        )

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"

    def test_start_without_any_shard_fails_before_queueing(self, training: TrainingContext) -> None:
        training.shard.unlink()
        training.shard.with_suffix(".idx").unlink()

        response = training.start()

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"

    def test_start_with_explicit_shard(self, training: TrainingContext) -> None:
        response = training.start(trainShards=[str(training.shard)])

        assert response.status_code == 202
        assert response.get_json()["status"] == "completed"

    def test_start_rejects_shard_outside_the_corpus(
        self, training: TrainingContext, tmp_path: Path
    ) -> None:
        outsideShard = writeTinyShard(tmp_path / "outside", name="other.bin")

        response = training.start(trainShards=[str(outsideShard)])

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"
        assert training.checkpointRepo.count() == 0

    def test_start_queues_a_job_without_running_it(self, deferredTraining: TrainingContext) -> None:
        response = deferredTraining.start()

        assert response.status_code == 202
        payload = response.get_json()
        assert payload["status"] == "pending"
        assert payload["result"] is None
        assert len(deferredTraining.pool.tasks) == 1


class TestTrainingControllerJobs:
    """Job listing, inspection and cancellation."""

    def test_list_jobs_returns_created_job(self, training: TrainingContext) -> None:
        created = training.start().get_json()

        response = training.client.get("/api/training/jobs", headers=AUTH_HEADERS)

        assert response.status_code == 200
        assert [job["id"] for job in response.get_json()] == [created["id"]]

    @pytest.mark.parametrize("query", ["limit=zero", "limit=0", "limit=201"])
    def test_list_jobs_rejects_invalid_limit(self, training: TrainingContext, query: str) -> None:
        response = training.client.get(
            f"/api/training/jobs?{query}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"

    def test_get_job(self, training: TrainingContext) -> None:
        created = training.start().get_json()

        response = training.client.get(
            f"/api/training/jobs/{created['id']}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        assert response.get_json()["id"] == created["id"]

    def test_get_unknown_job_returns_404(self, training: TrainingContext) -> None:
        response = training.client.get(
            "/api/training/jobs/unknown",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 404
        assert errorCode(response) == "RESOURCE_NOT_FOUND"

    def test_cancel_pending_job(self, deferredTraining: TrainingContext) -> None:
        created = deferredTraining.start().get_json()

        response = deferredTraining.client.post(
            f"/api/training/jobs/{created['id']}/cancel",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["status"] == "cancelled"
        assert payload["progress"]["cancelRequested"] is True

    def test_cancel_completed_job_returns_409(self, training: TrainingContext) -> None:
        created = training.start().get_json()

        response = training.client.post(
            f"/api/training/jobs/{created['id']}/cancel",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 409
        assert errorCode(response) == "INVALID_JOB_STATE"

    def test_cancel_unknown_job_returns_404(self, training: TrainingContext) -> None:
        response = training.client.post(
            "/api/training/jobs/unknown/cancel",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 404

    def test_history_returns_jsonl_entries(self, training: TrainingContext) -> None:
        created = training.start().get_json()
        checkpointDir = Path(created["result"]["checkpointDir"])
        logFile = checkpointDir / "training_log.jsonl"
        logFile.write_text(
            '{"step":1,"train/loss":0.5}\nnot-json\n{"step":2,"train/loss":0.25}\n',
            encoding="utf-8",
        )

        response = training.client.get(
            f"/api/training/jobs/{created['id']}/history",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        history = response.get_json()["history"]
        assert [entry["step"] for entry in history] == [1, 2]

    def test_history_unknown_job_returns_404(self, training: TrainingContext) -> None:
        response = training.client.get(
            "/api/training/jobs/unknown/history",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 404

    def test_stream_completed_job_returns_final_event(self, training: TrainingContext) -> None:
        created = training.start().get_json()

        response = training.client.get(
            f"/api/training/jobs/{created['id']}/stream",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        assert response.mimetype == "text/event-stream"
        assert "final" in response.get_data(as_text=True)

    def test_evaluate_pending_job_without_checkpoint_returns_validation_error(
        self, deferredTraining: TrainingContext
    ) -> None:
        created = deferredTraining.start().get_json()

        response = deferredTraining.client.post(
            f"/api/training/jobs/{created['id']}/evaluate",
            headers=AUTH_HEADERS,
            json={"prompt": "Hello"},
        )

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"


class TestTrainingControllerResume:
    """Resuming a job from its latest checkpoint."""

    def test_resume_creates_a_new_completed_job(self, training: TrainingContext) -> None:
        created = training.start().get_json()

        response = training.client.post(
            f"/api/training/jobs/{created['id']}/resume",
            headers=AUTH_HEADERS,
            json={"maxSteps": 2},
        )

        assert response.status_code == 202
        payload = response.get_json()
        assert payload["id"] != created["id"]
        assert payload["status"] == "completed"
        assert payload["resumeFrom"] is not None
        assert payload["result"]["steps"] == 2

    def test_resume_without_overrides(self, training: TrainingContext) -> None:
        created = training.start().get_json()

        response = training.client.post(
            f"/api/training/jobs/{created['id']}/resume",
            headers=AUTH_HEADERS,
            json={},
        )

        assert response.status_code == 202
        assert response.get_json()["status"] == "completed"

    def test_resume_rejects_invalid_overrides(self, training: TrainingContext) -> None:
        created = training.start().get_json()

        response = training.client.post(
            f"/api/training/jobs/{created['id']}/resume",
            headers=AUTH_HEADERS,
            json={"maxSteps": 0},
        )

        assert response.status_code == 400
        assert errorCode(response) == "VALIDATION_ERROR"

    def test_resume_with_unknown_checkpoint_returns_404(self, training: TrainingContext) -> None:
        created = training.start().get_json()

        response = training.client.post(
            f"/api/training/jobs/{created['id']}/resume",
            headers=AUTH_HEADERS,
            json={"checkpointId": "missing"},
        )

        assert response.status_code == 404
        assert errorCode(response) == "CHECKPOINT_NOT_FOUND"

    def test_resume_pending_job_without_checkpoint_returns_404(
        self, deferredTraining: TrainingContext
    ) -> None:
        created = deferredTraining.start().get_json()

        response = deferredTraining.client.post(
            f"/api/training/jobs/{created['id']}/resume",
            headers=AUTH_HEADERS,
            json={},
        )

        assert response.status_code == 404
        assert errorCode(response) == "CHECKPOINT_NOT_FOUND"

    def test_resume_unknown_job_returns_404(self, training: TrainingContext) -> None:
        response = training.client.post(
            "/api/training/jobs/unknown/resume",
            headers=AUTH_HEADERS,
            json={},
        )

        assert response.status_code == 404


class TestTrainingControllerCheckpoints:
    """Checkpoint listing and lookup."""

    def test_list_checkpoints(self, training: TrainingContext) -> None:
        training.start()

        response = training.client.get(
            "/api/training/checkpoints",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload
        assert all(entry["path"] for entry in payload)

    def test_list_checkpoints_filters_by_model_name(self, training: TrainingContext) -> None:
        training.start()

        found = training.client.get(
            "/api/training/checkpoints?modelName=tiny-test",
            headers=AUTH_HEADERS,
        )
        missing = training.client.get(
            "/api/training/checkpoints?modelName=other",
            headers=AUTH_HEADERS,
        )

        assert found.get_json()
        assert missing.get_json() == []

    @pytest.mark.parametrize("query", ["limit=0", "offset=-1", "offset=zero"])
    def test_list_checkpoints_rejects_invalid_bounds(
        self, training: TrainingContext, query: str
    ) -> None:
        response = training.client.get(
            f"/api/training/checkpoints?{query}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 400

    def test_get_checkpoint(self, training: TrainingContext) -> None:
        training.start()
        latest = training.checkpointRepo.findLatest()
        assert latest is not None

        response = training.client.get(
            f"/api/training/checkpoints/{latest.id}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        assert response.get_json()["id"] == latest.id

    def test_get_unknown_checkpoint_returns_404(self, training: TrainingContext) -> None:
        response = training.client.get(
            "/api/training/checkpoints/missing",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 404
        assert errorCode(response) == "CHECKPOINT_NOT_FOUND"
