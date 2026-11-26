# tests/integration/test_training_loop/test_trainingJobs.py
"""Training module through the HTTP API: jobs, checkpoints, presets, resume."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from flask.testing import FlaskClient

pytestmark = pytest.mark.integration

AUTH = {"Authorization": "Bearer dev-token"}


def trainingPayload(**overrides: Any) -> dict[str, Any]:
    """Small, fast training request on the tiny preset."""
    payload: dict[str, Any] = {
        "preset": "tiny",
        "modelName": "integration-tiny",
        "seqLen": 16,
        "batchSize": 2,
        "maxSteps": 2,
        "evalInterval": 0,
        "evalSteps": 1,
        "checkpointInterval": 0,
        "logInterval": 0,
        "dtype": "fp32",
        "compileModel": False,
        "scheduler": "constant",
        "warmupSteps": 0,
        "saveRng": False,
        "numWorkers": 0,
    }
    payload.update(overrides)
    return payload


def startTraining(client: FlaskClient, **overrides: Any) -> dict[str, Any]:
    """Post a training request and return the serialized job."""
    response = client.post(
        "/api/training/jobs",
        headers=AUTH,
        json=trainingPayload(**overrides),
    )
    assert response.status_code == 202, response.get_json()
    job: dict[str, Any] = response.get_json()
    return job


def test_training_job_runs_to_completion(
    client: FlaskClient,
    encodedShards: dict[str, Any],
) -> None:
    job = startTraining(client)

    assert job["jobType"] == "training"
    assert job["status"] == "completed", job
    assert job["error"] is None
    assert job["progress"]["step"] == 2
    assert job["progress"]["progress"] == 1.0
    assert job["progress"]["tokensSeen"] > 0
    assert job["progress"]["loss"] is not None
    assert job["result"]["steps"] == 2
    assert job["result"]["cancelled"] is False
    assert job["result"]["tokensSeen"] > 0


def test_training_writes_the_final_checkpoint(
    client: FlaskClient,
    encodedShards: dict[str, Any],
) -> None:
    job = startTraining(client)

    finalCheckpoint = Path(job["result"]["finalCheckpoint"])
    assert finalCheckpoint.is_file()
    assert finalCheckpoint.is_relative_to(Path(job["result"]["checkpointDir"]))
    assert Path(job["result"]["checkpointDir"]).name == job["id"]


def test_training_jobs_are_listed_and_fetchable(
    client: FlaskClient,
    encodedShards: dict[str, Any],
) -> None:
    job = startTraining(client)

    listResponse = client.get("/api/training/jobs", headers=AUTH)
    detailResponse = client.get(f"/api/training/jobs/{job['id']}", headers=AUTH)

    assert listResponse.status_code == 200
    jobs = listResponse.get_json()
    assert [entry["id"] for entry in jobs] == [job["id"]]
    assert detailResponse.status_code == 200
    assert detailResponse.get_json()["id"] == job["id"]


def test_unknown_training_job_returns_404(client: FlaskClient) -> None:
    response = client.get("/api/training/jobs/missing", headers=AUTH)

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_checkpoints_are_indexed_and_queryable(
    client: FlaskClient,
    encodedShards: dict[str, Any],
) -> None:
    job = startTraining(client)

    listResponse = client.get("/api/training/checkpoints", headers=AUTH)
    filterResponse = client.get(
        "/api/training/checkpoints?modelName=integration-tiny",
        headers=AUTH,
    )

    assert listResponse.status_code == 200
    checkpoints = listResponse.get_json()
    assert len(checkpoints) >= 1
    checkpointId = checkpoints[0]["id"]
    assert checkpointId == f"{job['id']}:final"
    assert filterResponse.get_json()[0]["modelName"] == "integration-tiny"

    detailResponse = client.get(
        f"/api/training/checkpoints/{checkpointId}",
        headers=AUTH,
    )
    assert detailResponse.status_code == 200
    detail = detailResponse.get_json()
    assert detail["id"] == checkpointId
    assert detail["modelConfig"]["vocabSize"] == 512
    assert detail["trainingConfig"]["modelName"] == "integration-tiny"


def test_resume_continues_from_the_latest_checkpoint(
    client: FlaskClient,
    encodedShards: dict[str, Any],
) -> None:
    firstJob = startTraining(client)

    response = client.post(
        f"/api/training/jobs/{firstJob['id']}/resume",
        headers=AUTH,
        json={"maxSteps": 3},
    )

    assert response.status_code == 202, response.get_json()
    resumed = response.get_json()
    assert resumed["id"] != firstJob["id"]
    assert resumed["resumeFrom"] == f"{firstJob['id']}:final"
    assert resumed["status"] == "completed", resumed
    assert resumed["progress"]["step"] == 3


def test_cancelling_a_completed_job_is_rejected(
    client: FlaskClient,
    encodedShards: dict[str, Any],
) -> None:
    job = startTraining(client)

    response = client.post(
        f"/api/training/jobs/{job['id']}/cancel",
        headers=AUTH,
    )

    assert response.status_code == 409
    error = response.get_json()["error"]
    assert error["code"] == "INVALID_JOB_STATE"
    assert error["details"]["status"] == "completed"


def test_presets_expose_the_built_in_architectures(client: FlaskClient) -> None:
    response = client.get("/api/training/presets", headers=AUTH)

    assert response.status_code == 200
    presets = {entry["name"]: entry for entry in response.get_json()}
    assert {"tiny", "125M", "350M", "760M", "1.3B"} <= set(presets)
    assert presets["tiny"]["modelConfig"]["vocabSize"] == 512
    assert presets["tiny"]["parameters"] > 0


def test_training_requires_available_shards(client: FlaskClient) -> None:
    response = client.post(
        "/api/training/jobs",
        headers=AUTH,
        json=trainingPayload(),
    )

    assert response.status_code == 400
    error = response.get_json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "shardDir" in error["details"]


def test_unknown_preset_is_rejected(client: FlaskClient) -> None:
    response = client.post(
        "/api/training/jobs",
        headers=AUTH,
        json=trainingPayload(preset="unknown"),
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_seq_len_above_the_context_window_is_rejected(client: FlaskClient) -> None:
    response = client.post(
        "/api/training/jobs",
        headers=AUTH,
        json=trainingPayload(seqLen=256),
    )

    assert response.status_code == 400
    error = response.get_json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"]["maxSeqLen"] == 128


def test_shard_outside_the_corpus_directory_is_rejected(
    client: FlaskClient,
    tmp_path: Path,
) -> None:
    outsideShard = tmp_path / "outside.bin"
    outsideShard.write_bytes(b"\x00\x00")

    response = client.post(
        "/api/training/jobs",
        headers=AUTH,
        json=trainingPayload(trainShards=[str(outsideShard)]),
    )

    assert response.status_code == 400
    error = response.get_json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert str(outsideShard) in error["details"]["path"]
