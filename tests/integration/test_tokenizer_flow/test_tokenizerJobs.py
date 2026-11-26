# tests/integration/test_tokenizer_flow/test_tokenizerJobs.py
"""Tokenizer module through the HTTP API: training, info, vocab, preview, encoding."""

from __future__ import annotations

from typing import Any

import pytest
from flask.testing import FlaskClient

from apps.modules.shared.config import Settings

pytestmark = pytest.mark.integration

AUTH = {"Authorization": "Bearer dev-token"}


def test_training_writes_the_tokenizer_artifacts(
    trainedTokenizer: dict[str, Any],
    tempSettings: Settings,
) -> None:
    assert trainedTokenizer["jobType"] == "tokenizer_training"
    assert trainedTokenizer["status"] == "completed"
    assert trainedTokenizer["progress"]["vocabSize"] > 4
    assert (tempSettings.tokenizerDir / "tokenizer.json").is_file()
    assert (tempSettings.tokenizerDir / "vocab_info.json").is_file()


def test_info_and_vocab_describe_the_trained_tokenizer(
    client: FlaskClient,
    trainedTokenizer: dict[str, Any],
) -> None:
    infoResponse = client.get("/api/tokenizer/info", headers=AUTH)
    vocabResponse = client.get("/api/tokenizer/vocab", headers=AUTH)

    assert infoResponse.status_code == 200
    info = infoResponse.get_json()
    assert info["exists"] is True
    assert info["vocabInfo"]["vocabSize"] == trainedTokenizer["progress"]["vocabSize"]

    assert vocabResponse.status_code == 200
    vocab = vocabResponse.get_json()
    assert vocab["exists"] is True
    assert len(vocab["tokens"]) == trainedTokenizer["progress"]["vocabSize"]
    tokens = {entry["token"] for entry in vocab["tokens"]}
    assert {"<|endoftext|>", "<|pad|>", "<|unk|>", "<|mask|>"} <= tokens


def test_preview_round_trips_text(
    client: FlaskClient,
    trainedTokenizer: dict[str, Any],
) -> None:
    text = "Le corpus de test sert au tokenizer."
    response = client.post(
        "/api/tokenizer/preview",
        headers=AUTH,
        json={"text": text},
    )

    assert response.status_code == 200
    preview = response.get_json()
    assert preview["text"] == text
    assert preview["tokenCount"] == len(preview["tokenIds"])
    assert preview["tokenCount"] > 0
    assert preview["characterCount"] == len(text)
    assert preview["compressionRatio"] > 0
    assert len(preview["tokens"]) == preview["tokenCount"]
    assert preview["decoded"].replace(" ", "") != ""


def test_training_without_clean_corpus_fails_cleanly(client: FlaskClient) -> None:
    response = client.post(
        "/api/tokenizer/train",
        headers=AUTH,
        json={"vocabSize": 256, "corpusSampleSize": 10, "languages": ["fr"]},
    )

    assert response.status_code == 202
    job = response.get_json()
    assert job["status"] == "failed"
    assert "Corpus vide" in job["error"]


def test_info_and_vocab_return_404_without_tokenizer(client: FlaskClient) -> None:
    infoResponse = client.get("/api/tokenizer/info", headers=AUTH)
    vocabResponse = client.get("/api/tokenizer/vocab", headers=AUTH)

    assert infoResponse.status_code == 404
    assert infoResponse.get_json() == {"exists": False}
    assert vocabResponse.status_code == 404
    assert vocabResponse.get_json() == {"exists": False, "tokens": []}


def test_preview_requires_a_trained_tokenizer(client: FlaskClient) -> None:
    response = client.post(
        "/api/tokenizer/preview",
        headers=AUTH,
        json={"text": "bonjour"},
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "TOKENIZER_NOT_FOUND"


def test_encode_requires_a_tokenizer_file(client: FlaskClient) -> None:
    response = client.post(
        "/api/tokenizer/encode",
        headers=AUTH,
        json={"shardSizeTokens": 1000},
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "TOKENIZER_NOT_FOUND"


def test_encode_writes_uint16_shards(
    encodedShards: dict[str, Any],
    tempSettings: Settings,
) -> None:
    progress = encodedShards["progress"]

    assert encodedShards["jobType"] == "corpus_encoding"
    assert encodedShards["status"] == "completed"
    assert progress["shardCount"] == 1
    assert progress["totalDocuments"] == 3
    assert progress["totalTokens"] > 0
    assert progress["avgTokensPerDoc"] > 0
    assert progress["languageDistribution"] == {"fr": 3}

    shardDir = tempSettings.corpusDir / "shards"
    shardFiles = sorted(shardDir.glob("shard_*.bin"))
    assert len(shardFiles) == 1
    assert shardFiles[0].stat().st_size == progress["totalTokens"] * 2
    assert shardFiles[0].with_suffix(".idx").is_file()


def test_encode_updates_the_corpus_statistics(
    client: FlaskClient,
    encodedShards: dict[str, Any],
) -> None:
    response = client.get("/api/corpus/stats", headers=AUTH)

    assert response.status_code == 200
    stats = response.get_json()
    assert stats["totalDocuments"] == 3
    assert stats["totalTokens"] == encodedShards["progress"]["totalTokens"]
    assert stats["languages"] == {"fr": 3}


def test_tokenizer_job_status_returns_the_job(
    client: FlaskClient,
    trainedTokenizer: dict[str, Any],
) -> None:
    response = client.get(
        f"/api/tokenizer/status/{trainedTokenizer['id']}",
        headers=AUTH,
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["id"] == trainedTokenizer["id"]
    assert payload["status"] == "completed"


def test_status_of_another_users_job_is_hidden(client: FlaskClient) -> None:
    response = client.get("/api/tokenizer/status/unknown", headers=AUTH)

    assert response.status_code == 404
    assert response.get_json()["error"]["details"] == {"jobId": "unknown"}
