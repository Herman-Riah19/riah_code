# tests/integration/conftest.py
"""Integration fixtures: real controllers, real repositories, synchronous jobs.

The integration suite exercises the HTTP layer end to end. Only two things are
replaced compared to production:

* every module-level ``settings`` points to a temporary directory;
* the background ``WorkerPool`` runs submitted jobs inline so an HTTP response
  already reflects the final job state (no polling, no flakiness).

Network scrapers are also replaced by an in-memory fake so the corpus pipeline
can run offline while still using the real cleaner, normalizer, quality filter,
deduplicator, markdown exporter and shard writer.
"""

from __future__ import annotations

from collections.abc import Iterator
from concurrent.futures import Future
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import torch
from flask import Flask
from flask.testing import FlaskClient

from apps.modules.corpus.controllers import corpusController
from apps.modules.corpus.models.corpusModel import RawDocument, ScrapeResult
from apps.modules.corpus.pipelines.baseScraper import BaseScraper
from apps.modules.model.controllers import inferenceController, trainingController
from apps.modules.model.ml.modelRunner import ModelRunner
from apps.modules.model.models.modelModel import Checkpoint, ModelConfig
from apps.modules.model.repositories.checkpointRepository import CheckpointRepository
from apps.modules.shared.config import Settings
from apps.modules.shared.decorators import auth
from apps.modules.tokenizer.controllers import tokenizerController
from run import createApp

FAKE_DOCUMENT_TEXTS: tuple[str, ...] = (
    (
        "Riah Code assemble un corpus de textes varies pour entrainer des modeles de "
        "langage. Chaque document respecte les seuils de qualite et contient suffisamment "
        "de mots distincts. Les phrases restent naturelles afin de passer le filtre sans "
        "etre rejetees par le pipeline."
    ),
    (
        "Le pipeline nettoie le balisage HTML avant de normaliser les espaces et les "
        "caracteres de controle. Un document trop court ou trop bruite est ecarte "
        "automatiquement par le filtre de qualite du corpus."
    ),
    (
        "Le tokenizer apprend des paires de caracteres frequentes puis produit un "
        "vocabulaire compact. Les shards binaires conservent les identifiants de tokens "
        "necessaires pour entrainer le modele de langage."
    ),
)

AUTH_HEADERS = {"Authorization": "Bearer dev-token"}
ALLOWED_ORIGIN = "http://localhost:5173"


class SyncWorkerPool:
    """Execute every submitted job inline, mimicking a fast worker pool."""

    def __init__(self, maxWorkers: int = 4) -> None:
        self.maxWorkers = maxWorkers

    def submit(self, task: Any, *args: Any) -> Future[Any]:
        """Run the task immediately and wrap its outcome in a resolved future."""
        future: Future[Any] = Future()
        try:
            future.set_result(task(*args))
        except Exception as error:  # noqa: BLE001 - the future carries the failure
            future.set_exception(error)
        return future


class FakeScraper(BaseScraper):
    """Persist a fixed set of documents instead of hitting the network."""

    def __init__(self, documents: list[RawDocument]) -> None:
        self._documents = documents

    def scrape(
        self,
        corpusRepo: Any,
    ) -> ScrapeResult:
        """Store the documents and report how many were handled."""
        saved = corpusRepo.saveRaw(self._documents)
        return ScrapeResult(
            documentsScraped=len(self._documents),
            documentsSaved=saved,
        )


class ExplodingScraper(BaseScraper):
    """Raise on purpose so the job failure path can be asserted."""

    def scrape(self, corpusRepo: Any) -> ScrapeResult:
        """Always fail."""
        raise RuntimeError("source indisponible")


_CONTAINER_ATTRIBUTES: dict[type[Any], tuple[str, ...]] = {
    corpusController.CorpusContainer: (
        "_corpusRepository",
        "_jobRepository",
        "_workerPool",
        "_service",
    ),
    tokenizerController.TokenizerContainer: (
        "_tokenizerRepository",
        "_corpusRepository",
        "_jobRepository",
        "_workerPool",
        "_service",
    ),
    trainingController.TrainingContainer: (
        "_checkpointRepository",
        "_tokenizerRepository",
        "_corpusRepository",
        "_jobRepository",
        "_workerPool",
        "_service",
    ),
    inferenceController.InferenceContainer: (
        "_checkpointRepository",
        "_tokenizerRepository",
        "_service",
    ),
}


def resetContainers() -> None:
    """Drop every cached repository/service so tests stay isolated."""
    for container, attributes in _CONTAINER_ATTRIBUTES.items():
        for attribute in attributes:
            setattr(container, attribute, None)


def buildFakeDocuments() -> list[RawDocument]:
    """Return three unique French documents plus one exact duplicate."""
    documents = [
        RawDocument.create(
            source="wikipedia",
            url=f"https://example.test/article/{index}",
            language="fr",
            text=text,
            metadata={"index": index},
        )
        for index, text in enumerate(FAKE_DOCUMENT_TEXTS)
    ]
    duplicate = RawDocument.create(
        source="wikipedia",
        url="https://example.test/article/duplicate",
        language="fr",
        text=FAKE_DOCUMENT_TEXTS[0],
        metadata={"index": 99},
    )
    return [*documents, duplicate]


@pytest.fixture
def tempSettings(tmp_path: Path) -> Settings:
    """Isolated settings rooted in the pytest temporary directory."""
    return Settings(
        dataDir=tmp_path / "data",
        logsDir=tmp_path / "logs",
        databaseUrl=f"sqlite:///{tmp_path / 'app.db'}",
        checkpointDir=tmp_path / "checkpoints",
        tensorboardDir=tmp_path / "tensorboard",
        corpusDir=tmp_path / "corpus",
        bibleDir=tmp_path / "bible",
        tokenizerDir=tmp_path / "tokenizer",
        chatHistoryDir=tmp_path / "chat",
        appEnv="testing",
        appVersion="0.0.0-test",
        debug=True,
        corsOrigins=[ALLOWED_ORIGIN],
        rateLimitRequests=1000,
    )


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch, tempSettings: Settings) -> Iterator[Flask]:
    """Flask application wired on temporary settings and synchronous workers."""
    modules = (
        corpusController,
        tokenizerController,
        trainingController,
        inferenceController,
    )
    for module in modules:
        monkeypatch.setattr(module, "settings", tempSettings)
        if hasattr(module, "WorkerPool"):
            monkeypatch.setattr(module, "WorkerPool", SyncWorkerPool)
    monkeypatch.setattr(auth, "settings", tempSettings)

    resetContainers()
    application = createApp(tempSettings)
    application.testing = True
    try:
        yield application
    finally:
        resetContainers()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """HTTP client bound to the integration application."""
    return app.test_client()


@pytest.fixture
def authHeaders() -> dict[str, str]:
    """Bearer token accepted while debug mode is enabled."""
    return dict(AUTH_HEADERS)


@pytest.fixture
def fakeCorpus(monkeypatch: pytest.MonkeyPatch) -> list[RawDocument]:
    """Replace the network scrapers by the in-memory document set."""
    documents = buildFakeDocuments()

    def buildScrapers(cls: type[Any], config: Any) -> list[BaseScraper]:
        return [FakeScraper(documents)]

    monkeypatch.setattr(
        corpusController.CorpusContainer,
        "buildScrapers",
        classmethod(buildScrapers),
    )
    return documents


@pytest.fixture
def corpusJob(
    client: FlaskClient,
    authHeaders: dict[str, str],
    fakeCorpus: list[RawDocument],
    tempSettings: Settings,
) -> dict[str, Any]:
    """Run the corpus pipeline once through the HTTP API."""
    response = client.post(
        "/api/corpus/pipeline/start",
        headers=authHeaders,
        json={
            "sources": ["wikipedia"],
            "languages": ["fr"],
            "outputDir": str(tempSettings.corpusDir / "pipeline"),
            "shardSizeTokens": 1000,
            "numWorkers": 1,
            "batchSize": 10,
            "maxArticlesPerLang": 10,
        },
    )
    assert response.status_code == 202, response.get_json()
    job: dict[str, Any] = response.get_json()
    assert job["status"] == "completed", job
    return job


@pytest.fixture
def trainedTokenizer(
    client: FlaskClient,
    authHeaders: dict[str, str],
    corpusJob: dict[str, Any],
) -> dict[str, Any]:
    """Train a BPE tokenizer through the HTTP API on the fake corpus."""
    response = client.post(
        "/api/tokenizer/train",
        headers=authHeaders,
        json={
            "vocabSize": 256,
            "minFrequency": 1,
            "corpusSampleSize": 50,
            "languages": ["fr"],
            "numThreads": 1,
        },
    )
    assert response.status_code == 202, response.get_json()
    job: dict[str, Any] = response.get_json()
    assert job["status"] == "completed", job
    return job


@pytest.fixture
def encodedShards(
    client: FlaskClient,
    authHeaders: dict[str, str],
    trainedTokenizer: dict[str, Any],
) -> dict[str, Any]:
    """Encode the clean corpus into uint16 shards through the HTTP API."""
    response = client.post(
        "/api/tokenizer/encode",
        headers=authHeaders,
        json={"shardSizeTokens": 1000, "languages": ["fr"]},
    )
    assert response.status_code == 202, response.get_json()
    job: dict[str, Any] = response.get_json()
    assert job["status"] == "completed", job
    return job


@pytest.fixture
def seededCheckpoint(tempSettings: Settings) -> Checkpoint:
    """Persist a tiny checkpoint whose EOS id is out of vocabulary.

    Using an unreachable ``eosTokenId`` keeps generation deterministic: the
    sampler never stops early, so exactly ``maxTokens`` tokens are produced.
    """
    config = ModelConfig(
        vocabSize=512,
        maxSeqLen=32,
        nLayers=2,
        nHeads=2,
        dim=16,
        dtype="fp32",
        eosTokenId=999,
    )
    torch.manual_seed(7)
    runner = ModelRunner(config, device=torch.device("cpu"))
    checkpointDir = tempSettings.checkpointDir / "seed"
    path = checkpointDir / "checkpoint_best.pt"
    runner.saveCheckpoint(path, step=1, epoch=0, extra={"modelName": "seed"})

    repository = CheckpointRepository(tempSettings.checkpointDir)
    checkpoint = Checkpoint(
        id="seed:best",
        path=path,
        step=1,
        epoch=0,
        loss=1.0,
        modelConfig=config,
        createdAt=datetime.now(UTC),
        isBest=True,
        modelName="seed",
        metadata={"tag": "best"},
    )
    return repository.save(checkpoint)
