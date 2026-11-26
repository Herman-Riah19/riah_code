# tests/unit/test_model/test_modelRepository.py
"""Tests for the model repository - presets and named JSON configs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tinyModel import tinyModelConfig

from apps.modules.model.models.modelModel import MODEL_PRESETS
from apps.modules.model.repositories.modelRepository import (
    CONFIG_DIR_NAME,
    ModelRepository,
)
from apps.modules.shared.kernel.exceptions import (
    ResourceNotFoundError,
    ValidationError,
)


@pytest.fixture
def repository(tmp_path: Path) -> ModelRepository:
    """Repository rooted in a temporary directory."""
    return ModelRepository(tmp_path)


class TestModelPresets:
    """Read access to the built-in architectures."""

    def test_list_presets_returns_every_builtin(self, repository: ModelRepository) -> None:
        assert repository.listPresets() == MODEL_PRESETS

    def test_list_presets_returns_a_copy(self, repository: ModelRepository) -> None:
        presets = repository.listPresets()
        presets.clear()

        assert repository.listPresets() == MODEL_PRESETS

    def test_get_preset(self, repository: ModelRepository) -> None:
        assert repository.getPreset("tiny") == MODEL_PRESETS["tiny"]

    def test_unknown_preset_raises(self, repository: ModelRepository) -> None:
        with pytest.raises(ValidationError, match="inconnu"):
            repository.getPreset("galactic")


class TestNamedConfigs:
    """Persistence of custom model configurations."""

    def test_config_directory_is_created(self, tmp_path: Path) -> None:
        ModelRepository(tmp_path)

        assert (tmp_path / CONFIG_DIR_NAME).is_dir()

    def test_save_writes_a_json_file(self, repository: ModelRepository) -> None:
        path = repository.saveConfig("custom", tinyModelConfig(dim=32))

        assert path.is_file()
        assert path.suffix == ".json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["dim"] == 32

    def test_load_round_trips(self, repository: ModelRepository) -> None:
        config = tinyModelConfig(dim=48, nLayers=3)

        repository.saveConfig("custom", config)
        restored = repository.loadConfig("custom")

        assert restored.toDict() == config.toDict()

    def test_saving_twice_overwrites(self, repository: ModelRepository) -> None:
        repository.saveConfig("custom", tinyModelConfig(dim=32))
        repository.saveConfig("custom", tinyModelConfig(dim=96))

        assert repository.loadConfig("custom").dim == 96
        assert repository.listConfigs() == ["custom"]

    def test_list_configs_is_sorted(self, repository: ModelRepository) -> None:
        for name in ("zeta", "alpha", "mu"):
            repository.saveConfig(name, tinyModelConfig())

        assert repository.listConfigs() == ["alpha", "mu", "zeta"]

    def test_delete_existing_config(self, repository: ModelRepository) -> None:
        repository.saveConfig("custom", tinyModelConfig())

        assert repository.deleteConfig("custom") is True
        assert repository.listConfigs() == []

    def test_delete_unknown_config_returns_false(self, repository: ModelRepository) -> None:
        assert repository.deleteConfig("missing") is False

    def test_load_unknown_config_raises(self, repository: ModelRepository) -> None:
        with pytest.raises(ResourceNotFoundError, match="introuvable"):
            repository.loadConfig("missing")

    def test_loaded_name_is_sanitized(self, repository: ModelRepository) -> None:
        repository.saveConfig("safe-name_1", tinyModelConfig())

        assert repository.loadConfig("safe-name_1").dim == tinyModelConfig().dim


class TestConfigNameValidation:
    """Reject names that could escape the config directory."""

    @pytest.mark.parametrize(
        "name",
        [
            "",
            "a" * 65,
            "bad/name",
            "bad name",
            "..",
            "../escape",
            "na.me",
            "na:me",
        ],
    )
    def test_save_rejects_invalid_names(self, repository: ModelRepository, name: str) -> None:
        with pytest.raises(ValidationError, match="invalide"):
            repository.saveConfig(name, tinyModelConfig())

    @pytest.mark.parametrize("name", ["", "../escape"])
    def test_load_rejects_invalid_names(self, repository: ModelRepository, name: str) -> None:
        with pytest.raises(ValidationError, match="invalide"):
            repository.loadConfig(name)

    def test_delete_rejects_invalid_names(self, repository: ModelRepository) -> None:
        with pytest.raises(ValidationError, match="invalide"):
            repository.deleteConfig("../escape")

    def test_valid_name_of_maximal_length(self, repository: ModelRepository) -> None:
        name = "a" * 64

        repository.saveConfig(name, tinyModelConfig())

        assert repository.listConfigs() == [name]
