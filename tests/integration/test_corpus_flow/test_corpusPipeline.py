# tests/integration/test_corpus_flow/test_corpusPipeline.py
"""Corpus module through the HTTP API: pipeline, stats, datasets, sources."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from flask.testing import FlaskClient

from apps.modules.corpus.controllers import corpusController
from apps.modules.corpus.models.corpusModel import ScrapeResult
from apps.modules.corpus.pipelines.baseScraper import BaseScraper
from apps.modules.shared.config import Settings

pytestmark = pytest.mark.integration

AUTH = {"Authorization": "Bearer dev-token"}


class ExplodingScraper(BaseScraper):
    """Scraper failing on purpose to exercise the job error path."""

    def scrape(self, outputDir: Path, corpusRepo: Any) -> ScrapeResult:
        """Always fail with a readable message."""
        raise RuntimeError("source indisponible")


def test_pipeline_runs_every_stage_and_reports_counts(
    corpusJob: dict[str, Any],
    tempSettings: Settings,
) -> None:
    progress = corpusJob["progress"]

    assert corpusJob["status"] == "completed"
    assert corpusJob["error"] is None
    assert progress["documentsScraped"] == 4
    assert progress["documentsCleaned"] == 4
    assert progress["documentsDeduplicated"] == 1
    assert progress["documentsExported"] == 3
    assert progress["shardsWritten"] == 1
    assert progress["totalTokens"] > 0


def test_pipeline_writes_shards_markdown_and_checkpoints(
    corpusJob: dict[str, Any],
    tempSettings: Settings,
) -> None:
    pipelineDir = tempSettings.corpusDir / "pipeline"
    checkpointDir = tempSettings.corpusDir / "checkpoints"
    markdownDir = tempSettings.corpusDir / "markdown" / "wikipedia" / "fr"

    assert (pipelineDir / "shard_000001.bin").is_file()
    assert (pipelineDir / "shard_000001.idx").is_file()
    assert len(list(markdownDir.glob("*.md"))) == 3
    assert {path.name for path in checkpointDir.glob("*.json")} == {
        "scrape.json",
        "dedup.json",
        "shard.json",
    }


def test_stats_aggregate_the_shard_index(
    client: FlaskClient,
    corpusJob: dict[str, Any],
) -> None:
    response = client.get("/api/corpus/stats", headers=AUTH)

    assert response.status_code == 200
    stats = response.get_json()
    assert stats["totalDocuments"] == 3
    assert stats["totalTokens"] == corpusJob["progress"]["totalTokens"]
    assert stats["totalSizeBytes"] > 0
    assert stats["languages"] == {"fr": 3}


def test_datasets_group_markdown_by_source(client: FlaskClient, corpusJob: dict[str, Any]) -> None:
    response = client.get("/api/corpus/datasets", headers=AUTH)

    assert response.status_code == 200
    datasets = response.get_json()["datasets"]
    assert len(datasets) == 1
    assert datasets[0]["source"] == "wikipedia"
    assert datasets[0]["languages"] == ["fr"]
    assert datasets[0]["documentCount"] == 3
    assert datasets[0]["totalSizeBytes"] > 0


def test_sources_describe_the_three_scrapers(client: FlaskClient) -> None:
    response = client.get("/api/corpus/sources", headers=AUTH)

    assert response.status_code == 200
    sources = {source["id"]: source for source in response.get_json()["sources"]}
    assert set(sources) == {"wikipedia", "bible", "valtorta"}
    assert sources["wikipedia"]["languages"] == ["fr", "en", "es", "de"]
    assert sources["bible"]["languages"] == ["fr", "en"]
    assert sources["valtorta"]["languages"] == ["fr"]


def test_pipeline_status_returns_the_owned_job(
    client: FlaskClient,
    corpusJob: dict[str, Any],
) -> None:
    response = client.get(f"/api/corpus/pipeline/{corpusJob['id']}/status", headers=AUTH)

    assert response.status_code == 200
    assert response.get_json()["id"] == corpusJob["id"]


def test_pipeline_can_be_resumed(client: FlaskClient, corpusJob: dict[str, Any]) -> None:
    response = client.post(
        f"/api/corpus/pipeline/{corpusJob['id']}/resume",
        headers=AUTH,
    )

    assert response.status_code == 200
    job = response.get_json()
    assert job["id"] == corpusJob["id"]
    assert job["status"] == "completed"
    assert job["finishedAt"] is not None


def test_pipeline_failure_is_captured_in_the_job(
    client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
    tempSettings: Settings,
) -> None:
    def buildScrapers(cls: type[Any], config: Any) -> list[BaseScraper]:
        return [ExplodingScraper()]

    monkeypatch.setattr(
        corpusController.CorpusContainer,
        "buildScrapers",
        classmethod(buildScrapers),
    )

    response = client.post(
        "/api/corpus/pipeline/start",
        headers=AUTH,
        json={
            "sources": ["wikipedia"],
            "languages": ["fr"],
            "outputDir": str(tempSettings.corpusDir / "failing"),
            "shardSizeTokens": 1000,
        },
    )

    assert response.status_code == 202
    job = response.get_json()
    assert job["status"] == "failed"
    assert "source indisponible" in job["error"]


def test_resume_of_an_unknown_job_returns_404(client: FlaskClient) -> None:
    response = client.post("/api/corpus/pipeline/missing/resume", headers=AUTH)

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_corpus_artifacts_stay_inside_the_temporary_directory(
    corpusJob: dict[str, Any],
    tempSettings: Settings,
) -> None:
    shardPaths = list((tempSettings.corpusDir / "pipeline").glob("*.bin"))
    assert shardPaths
    assert all(Path(path).is_relative_to(tempSettings.corpusDir) for path in shardPaths)
