# tests/unit/test_model/test_shardedDataset.py
"""Tests for the sharded token iterable dataset."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import torch
from tinyShards import makeTokenDocuments, writeTinyShard, writeTokenShard

from apps.modules.model.pipelines import shardedDataset
from apps.modules.model.pipelines.shardedDataset import ShardedTokenDataset


def collect(dataset: ShardedTokenDataset) -> list[dict[str, torch.Tensor]]:
    """Materialize every window yielded by a dataset."""
    return list(dataset)


def firstTokens(windows: list[dict[str, torch.Tensor]]) -> list[int]:
    """Return the first input token of every window, in order."""
    return [int(window["input_ids"][0]) for window in windows]


class FakeWorkerInfo:
    """Stand-in for `torch.utils.data.get_worker_info()`."""

    def __init__(self, workerId: int, numWorkers: int) -> None:
        self.id = workerId
        self.num_workers = numWorkers


class TestShardedTokenDatasetWindows:
    """Window shapes, shifted labels and document boundaries."""

    def test_len_counts_complete_windows(self, tmp_path: Path) -> None:
        shard = writeTinyShard(tmp_path, documentCount=3, documentLength=9)
        dataset = ShardedTokenDataset([shard], seqLen=4)

        # (9 - 1) // 4 == 2 windows per document.
        assert len(dataset) == 6
        assert len(collect(dataset)) == 6

    def test_window_labels_are_shifted_by_one(self, tmp_path: Path) -> None:
        shard = writeTinyShard(tmp_path, documentCount=1, documentLength=9)
        window = next(iter(ShardedTokenDataset([shard], seqLen=4)))

        assert window["input_ids"].shape == (4,)
        assert window["labels"].shape == (4,)
        torch.testing.assert_close(window["input_ids"][1:], window["labels"][:-1])

    def test_labels_match_the_following_token(self, tmp_path: Path) -> None:
        shard = writeTokenShard(tmp_path / "shard.bin", [list(range(10))], vocabSize=16)
        window = next(iter(ShardedTokenDataset([shard], seqLen=4)))

        torch.testing.assert_close(window["input_ids"], torch.arange(0, 4))
        torch.testing.assert_close(window["labels"], torch.arange(1, 5))

    def test_token_outside_model_vocabulary_fails_before_device_transfer(
        self, tmp_path: Path
    ) -> None:
        shard = writeTokenShard(
            tmp_path / "shard.bin",
            [[1, 2, 3, 4, 31999]],
            vocabSize=32_000,
        )
        dataset = ShardedTokenDataset([shard], seqLen=4, vocabSize=512)

        with pytest.raises(ValueError, match=r"Token ID 31999.*vocabulary size 512"):
            next(iter(dataset))

    def test_document_of_exactly_seq_len_plus_one_yields_one_window(self, tmp_path: Path) -> None:
        shard = writeTokenShard(tmp_path / "shard.bin", [list(range(5))], vocabSize=16)

        assert len(ShardedTokenDataset([shard], seqLen=4)) == 1

    def test_document_of_exactly_seq_len_yields_nothing(self, tmp_path: Path) -> None:
        shard = writeTokenShard(tmp_path / "shard.bin", [list(range(4))], vocabSize=16)

        assert len(ShardedTokenDataset([shard], seqLen=4)) == 0

    def test_documents_never_cross_boundaries(self, tmp_path: Path) -> None:
        documents = [list(range(100, 109)), list(range(200, 209))]
        shard = writeTokenShard(tmp_path / "shard.bin", documents, vocabSize=512)

        windows = collect(ShardedTokenDataset([shard], seqLen=4))

        assert len(windows) == 4
        firstDocument = windows[:2]
        secondDocument = windows[2:]
        assert all(int(window["labels"].max()) < 200 for window in firstDocument)
        assert all(int(window["input_ids"].min()) >= 200 for window in secondDocument)

    def test_short_documents_are_skipped(self, tmp_path: Path) -> None:
        documents = [[1, 2, 3], list(range(10)), [4, 5]]
        shard = writeTokenShard(tmp_path / "shard.bin", documents, vocabSize=16)

        assert len(collect(ShardedTokenDataset([shard], seqLen=4))) == 2

    def test_empty_shard_yields_nothing(self, tmp_path: Path) -> None:
        shard = writeTokenShard(tmp_path / "empty.bin", [])

        dataset = ShardedTokenDataset([shard], seqLen=4)

        assert len(dataset) == 0
        assert collect(dataset) == []
        assert dataset.totalTokens == 0

    def test_total_tokens(self, tmp_path: Path) -> None:
        shard = writeTinyShard(tmp_path, documentCount=2, documentLength=10)

        dataset = ShardedTokenDataset([shard], seqLen=4)

        assert dataset.totalTokens == 20
        assert dataset.shardPaths == [shard.resolve()]


class TestShardedTokenDatasetMultipleShards:
    """Concatenation of several shards and worker-level sharding."""

    def test_windows_cover_every_shard(self, tmp_path: Path) -> None:
        first = writeTokenShard(tmp_path / "a.bin", [list(range(100, 109))], 512)
        second = writeTokenShard(tmp_path / "b.bin", [list(range(200, 209))], 512)

        dataset = ShardedTokenDataset([first, second], seqLen=4)
        windows = collect(dataset)

        assert len(dataset) == 4
        assert len(windows) == 4
        assert int(windows[0]["input_ids"][0]) == 100
        assert int(windows[-1]["input_ids"][0]) >= 200

    def test_workers_split_shards_without_overlap(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        first = writeTokenShard(tmp_path / "a.bin", [list(range(100, 109))], 512)
        second = writeTokenShard(tmp_path / "b.bin", [list(range(200, 209))], 512)
        dataset = ShardedTokenDataset([first, second], seqLen=4)

        monkeypatch.setattr(shardedDataset, "get_worker_info", lambda: FakeWorkerInfo(0, 2))
        workerZero = collect(dataset)

        monkeypatch.setattr(shardedDataset, "get_worker_info", lambda: FakeWorkerInfo(1, 2))
        workerOne = collect(dataset)

        assert len(workerZero) == 2
        assert len(workerOne) == 2
        assert all(int(window["input_ids"].min()) < 200 for window in workerZero)
        assert all(int(window["input_ids"].min()) >= 200 for window in workerOne)

    def test_single_worker_receives_every_shard(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        first = writeTokenShard(tmp_path / "a.bin", [list(range(100, 109))], 512)
        second = writeTokenShard(tmp_path / "b.bin", [list(range(200, 209))], 512)
        dataset = ShardedTokenDataset([first, second], seqLen=4)

        monkeypatch.setattr(shardedDataset, "get_worker_info", lambda: FakeWorkerInfo(0, 1))

        assert len(collect(dataset)) == 4


class TestShardedTokenDatasetPaths:
    """Path normalization and index validation."""

    def test_missing_suffix_is_resolved(self, tmp_path: Path) -> None:
        shard = writeTinyShard(tmp_path, name="shard_000001.bin")
        dataset = ShardedTokenDataset([shard.with_suffix("")], seqLen=4)

        assert dataset.shardPaths == [shard.resolve()]

    def test_idx_suffix_is_accepted(self, tmp_path: Path) -> None:
        shard = writeTinyShard(tmp_path, name="shard_000001.bin")
        dataset = ShardedTokenDataset([shard.with_suffix(".idx")], seqLen=4)

        assert dataset.shardPaths == [shard.resolve()]

    def test_missing_shard_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="Shard introuvable"):
            ShardedTokenDataset([tmp_path / "missing.bin"], seqLen=4)

    def test_missing_index_raises(self, tmp_path: Path) -> None:
        shard = writeTinyShard(tmp_path)
        shard.with_suffix(".idx").unlink()

        with pytest.raises(FileNotFoundError, match="Index de shard introuvable"):
            ShardedTokenDataset([shard], seqLen=4)

    def test_index_beyond_the_shard_raises(self, tmp_path: Path) -> None:
        shard = writeTokenShard(tmp_path / "shard.bin", [[1, 2, 3, 4]])
        shard.with_suffix(".idx").write_text(
            json.dumps({"documentId": "bad", "offset": 0, "length": 99}) + "\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="incoherent"):
            ShardedTokenDataset([shard], seqLen=2)

    def test_negative_offset_raises(self, tmp_path: Path) -> None:
        shard = writeTokenShard(tmp_path / "shard.bin", [[1, 2, 3, 4]])
        shard.with_suffix(".idx").write_text(
            json.dumps({"documentId": "bad", "offset": -1, "length": 2}) + "\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="incoherent"):
            ShardedTokenDataset([shard], seqLen=2)

    def test_malformed_index_line_raises(self, tmp_path: Path) -> None:
        shard = writeTinyShard(tmp_path)
        shard.with_suffix(".idx").write_text("{not-json\n", encoding="utf-8")

        with pytest.raises(ValueError):
            ShardedTokenDataset([shard], seqLen=4)

    def test_non_integer_index_field_raises(self, tmp_path: Path) -> None:
        shard = writeTokenShard(tmp_path / "shard.bin", [[1, 2, 3, 4]])
        shard.with_suffix(".idx").write_text(
            json.dumps({"documentId": "bad", "offset": 0, "length": "four"}) + "\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError):
            ShardedTokenDataset([shard], seqLen=2)

    def test_blank_index_lines_are_ignored(self, tmp_path: Path) -> None:
        shard = writeTokenShard(tmp_path / "shard.bin", [[1, 2, 3, 4, 5]])
        shard.with_suffix(".idx").write_text(
            "\n" + json.dumps({"documentId": "doc", "offset": 0, "length": 5}) + "\n\n",
            encoding="utf-8",
        )

        assert len(ShardedTokenDataset([shard], seqLen=2)) == 2

    def test_invalid_seq_len_raises(self, tmp_path: Path) -> None:
        shard = writeTinyShard(tmp_path)

        with pytest.raises(ValueError, match="seqLen"):
            ShardedTokenDataset([shard], seqLen=0)

    def test_negative_seed_raises(self, tmp_path: Path) -> None:
        shard = writeTinyShard(tmp_path)

        with pytest.raises(ValueError, match="seed"):
            ShardedTokenDataset([shard], seqLen=4, seed=-1)


class TestShardedTokenDatasetShuffle:
    """Deterministic shuffling driven by the epoch."""

    def test_same_seed_and_epoch_give_same_order(self, tmp_path: Path) -> None:
        shard = writeTinyShard(tmp_path, documentCount=6, documentLength=13)

        first = firstTokens(collect(ShardedTokenDataset([shard], seqLen=4, shuffle=True, seed=5)))
        second = firstTokens(collect(ShardedTokenDataset([shard], seqLen=4, shuffle=True, seed=5)))

        assert first == second

    def test_different_seeds_give_different_orders(self, tmp_path: Path) -> None:
        shard = writeTinyShard(tmp_path, documentCount=6, documentLength=13)

        first = firstTokens(collect(ShardedTokenDataset([shard], seqLen=4, shuffle=True, seed=5)))
        second = firstTokens(collect(ShardedTokenDataset([shard], seqLen=4, shuffle=True, seed=6)))

        assert sorted(first) == sorted(second)
        assert first != second

    def test_epoch_changes_the_order(self, tmp_path: Path) -> None:
        shard = writeTinyShard(tmp_path, documentCount=6, documentLength=13)
        dataset = ShardedTokenDataset([shard], seqLen=4, shuffle=True, seed=5)

        firstPass = firstTokens(collect(dataset))
        dataset.setEpoch(1)
        secondPass = firstTokens(collect(dataset))

        assert dataset.epoch == 1
        assert sorted(firstPass) == sorted(secondPass)
        assert firstPass != secondPass

    def test_unshuffled_order_is_source_order(self, tmp_path: Path) -> None:
        documents = makeTokenDocuments(documentCount=3, documentLength=9)
        shard = writeTokenShard(tmp_path / "shard.bin", documents, vocabSize=64)

        windows = collect(ShardedTokenDataset([shard], seqLen=4))

        assert int(windows[0]["input_ids"][0]) == documents[0][0]
        assert int(windows[2]["input_ids"][0]) == documents[1][0]
