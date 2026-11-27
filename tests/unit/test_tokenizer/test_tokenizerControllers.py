# tests/unit/test_tokenizer/test_controllers.py
"""Tests for the tokenizer HTTP controller."""

from datetime import UTC, datetime

import pytest
from flask import Flask, jsonify
from tinyCorpus import TINY_CORPUS_TEXTS

from apps.modules.corpus.models.corpusModel import CleanDocument
from apps.modules.corpus.repositories.corpusRepository import CorpusRepository
from apps.modules.shared.kernel.exceptions import RiahAppError
from apps.modules.shared.kernel.job import Job, JobRepository, JobType
from apps.modules.tokenizer.controllers.tokenizerController import (
    TokenizerContainer,
    tokenizerBlueprint,
)
from apps.modules.tokenizer.repositories.tokenizerRepository import TokenizerRepository
from apps.modules.tokenizer.services.tokenizerService import TokenizerService

AUTH_HEADERS = {"Authorization": "Bearer dev-token"}


class InlineWorkerPool:
    """Run submitted jobs immediately, in the calling thread."""

    def submit(self, task, *args):
        task(*args)


def makeCleanDocument(documentId: str, text: str) -> CleanDocument:
    """Build a clean document for the corpus repository."""
    return CleanDocument(
        id=documentId,
        source="wikipedia",
        language="fr",
        text=text,
        qualityScore=0.9,
        tokenCount=len(text.split()),
        cleanedAt=datetime.now(UTC),
    )


@pytest.fixture
def container(tmp_path, monkeypatch) -> dict:
    """Configure the controller container with temporary repositories."""
    tokenizerRepo = TokenizerRepository(tmp_path / "tokenizer")
    corpusRepo = CorpusRepository(tmp_path / "corpus")
    jobRepo = JobRepository()
    service = TokenizerService(
        tokenizerRepo=tokenizerRepo,
        corpusRepo=corpusRepo,
        jobRepo=jobRepo,
        workerPool=InlineWorkerPool(),
    )
    monkeypatch.setattr(TokenizerContainer, "_tokenizerRepository", tokenizerRepo)
    monkeypatch.setattr(TokenizerContainer, "_corpusRepository", corpusRepo)
    monkeypatch.setattr(TokenizerContainer, "_jobRepository", jobRepo)
    monkeypatch.setattr(TokenizerContainer, "_workerPool", InlineWorkerPool())
    monkeypatch.setattr(TokenizerContainer, "_service", service)

    application = Flask(__name__)
    application.config.update(TESTING=True)

    @application.errorhandler(RiahAppError)
    def handleAppError(error: RiahAppError):
        response = jsonify(error.to_dict())
        response.status_code = error.statusCode
        return response

    application.register_blueprint(tokenizerBlueprint)
    return {
        "app": application,
        "tokenizerRepo": tokenizerRepo,
        "corpusRepo": corpusRepo,
        "jobRepo": jobRepo,
    }


@pytest.fixture
def client(container: dict):
    return container["app"].test_client()


class TestTokenizerController:
    """Blueprint wiring and HTTP contract."""

    def test_blueprint_exists(self) -> None:
        assert tokenizerBlueprint.name == "tokenizer"

    def test_blueprint_url_prefix(self) -> None:
        assert tokenizerBlueprint.url_prefix == "/api/tokenizer"

    def test_info_requires_auth(self, client) -> None:
        response = client.get("/api/tokenizer/info")

        assert response.status_code == 401

    def test_info_returns_404_without_tokenizer(self, client) -> None:
        response = client.get("/api/tokenizer/info", headers=AUTH_HEADERS)

        assert response.status_code == 404
        assert response.get_json() == {"exists": False}

    def test_train_rejects_invalid_payload(self, client) -> None:
        response = client.post(
            "/api/tokenizer/train",
            headers=AUTH_HEADERS,
            json={"vocabSize": 10},
        )

        assert response.status_code == 400
        assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"

    def test_train_then_info(self, client, container: dict) -> None:
        documents = [
            makeCleanDocument(f"doc-{index}", text) for index, text in enumerate(TINY_CORPUS_TEXTS)
        ]
        container["corpusRepo"].saveClean(documents)

        trainResponse = client.post(
            "/api/tokenizer/train",
            headers=AUTH_HEADERS,
            json={
                "vocabSize": 300,
                "minFrequency": 1,
                "corpusSampleSize": 100,
                "languages": ["fr"],
            },
        )

        assert trainResponse.status_code == 202
        trainedJob = trainResponse.get_json()
        assert trainedJob["jobType"] == "tokenizer_training"
        assert trainedJob["status"] == "completed"
        assert trainedJob["progress"]["vocabSize"] > 0

        statusResponse = client.get(
            f"/api/tokenizer/status/{trainedJob['id']}",
            headers=AUTH_HEADERS,
        )
        assert statusResponse.status_code == 200
        assert statusResponse.get_json()["status"] == "completed"

        infoResponse = client.get("/api/tokenizer/info", headers=AUTH_HEADERS)
        assert infoResponse.status_code == 200
        payload = infoResponse.get_json()
        assert payload["exists"] is True
        assert payload["vocabInfo"]["vocabSize"] == trainedJob["progress"]["vocabSize"]

    def test_encode_then_status(self, client, container: dict) -> None:
        documents = [
            makeCleanDocument(f"doc-{index}", text)
            for index, text in enumerate(TINY_CORPUS_TEXTS[:5])
        ]
        container["corpusRepo"].saveClean(documents)
        client.post(
            "/api/tokenizer/train",
            headers=AUTH_HEADERS,
            json={"vocabSize": 300, "minFrequency": 1, "languages": ["fr"]},
        )

        encodeResponse = client.post(
            "/api/tokenizer/encode",
            headers=AUTH_HEADERS,
            json={"shardSizeTokens": 1000},
        )

        assert encodeResponse.status_code == 202
        encodedJob = encodeResponse.get_json()
        assert encodedJob["jobType"] == "corpus_encoding"
        assert encodedJob["status"] == "completed"
        assert encodedJob["progress"]["totalDocuments"] == 5
        assert encodedJob["progress"]["shardCount"] >= 1

    def test_encode_rejects_path_traversal(self, client) -> None:
        response = client.post(
            "/api/tokenizer/encode",
            headers=AUTH_HEADERS,
            json={"tokenizerPath": "../../etc/passwd"},
        )

        assert response.status_code == 400
        assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"

    def test_status_of_unknown_job_returns_404(self, client) -> None:
        response = client.get(
            "/api/tokenizer/status/unknown",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 404

    def test_status_of_another_user_job_returns_404(
        self,
        client,
        container: dict,
    ) -> None:
        job = Job.create(
            jobType=JobType.TOKENIZER_TRAINING,
            config={},
            userId="another-user",
        )
        container["jobRepo"].save(job)

        response = client.get(
            f"/api/tokenizer/status/{job.id}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 404

    def test_preview_requires_tokenizer(self, client) -> None:
        response = client.post(
            "/api/tokenizer/preview",
            headers=AUTH_HEADERS,
            json={"text": "Bonjour le monde."},
        )

        assert response.status_code == 404

    def test_preview_rejects_empty_text(self, client) -> None:
        response = client.post(
            "/api/tokenizer/preview",
            headers=AUTH_HEADERS,
            json={"text": ""},
        )

        assert response.status_code == 400

    def test_preview_returns_tokens(self, client, container: dict) -> None:
        documents = [
            makeCleanDocument(f"doc-{index}", text) for index, text in enumerate(TINY_CORPUS_TEXTS)
        ]
        container["corpusRepo"].saveClean(documents)
        client.post(
            "/api/tokenizer/train",
            headers=AUTH_HEADERS,
            json={"vocabSize": 300, "minFrequency": 1, "languages": ["fr"]},
        )

        response = client.post(
            "/api/tokenizer/preview",
            headers=AUTH_HEADERS,
            json={"text": "Le petit chat dort."},
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["tokenCount"] > 0
        assert len(payload["tokens"]) == payload["tokenCount"]
        assert len(payload["tokenIds"]) == payload["tokenCount"]
        assert payload["decoded"].strip() == "Le petit chat dort."

    def test_vocab_requires_tokenizer(self, client):
        response = client.get(
            "/api/tokenizer/vocab",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 404
        assert response.get_json() == {"exists": False, "tokens": []}

    def test_vocab_returns_tokens(self, client, container: dict):
        documents = [
            makeCleanDocument(f"doc-{index}", text) for index, text in enumerate(TINY_CORPUS_TEXTS)
        ]
        container["corpusRepo"].saveClean(documents)
        client.post(
            "/api/tokenizer/train",
            headers=AUTH_HEADERS,
            json={"vocabSize": 300, "minFrequency": 1, "languages": ["fr"]},
        )

        response = client.get(
            "/api/tokenizer/vocab",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["exists"] is True
        assert len(payload["tokens"]) > 0
        first = payload["tokens"][0]
        assert set(first) == {"token", "tokenId"}
        assert first["tokenId"] == 0
        ids = [t["tokenId"] for t in payload["tokens"]]
        assert ids == sorted(ids)
