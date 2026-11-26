# apps/modules/model/repositories/modelRepository.py
"""Model repository - architecture presets and named JSON configs."""

from __future__ import annotations

import json
import re
from pathlib import Path

from apps.modules.shared.kernel.exceptions import ResourceNotFoundError, ValidationError

from ..models.modelModel import MODEL_PRESETS, ModelConfig

CONFIG_DIR_NAME = "configs"
_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class ModelRepository:
    """Expose built-in presets and persist custom model configs on disk."""

    def __init__(self, baseDir: Path) -> None:
        self._baseDir = baseDir
        self._configDir = baseDir / CONFIG_DIR_NAME
        self._configDir.mkdir(parents=True, exist_ok=True)

    @property
    def baseDir(self) -> Path:
        """Directory holding custom model configs."""
        return self._baseDir

    @staticmethod
    def listPresets() -> dict[str, ModelConfig]:
        """Return the built-in architecture presets."""
        return dict(MODEL_PRESETS)

    @staticmethod
    def getPreset(name: str) -> ModelConfig:
        """Return one built-in preset or raise `ValidationError`."""
        preset = MODEL_PRESETS.get(name)
        if preset is None:
            raise ValidationError(
                "Preset de modele inconnu",
                details={"name": name, "available": sorted(MODEL_PRESETS)},
            )
        return preset

    def saveConfig(self, name: str, config: ModelConfig) -> Path:
        """Persist a named model config as JSON."""
        path = self._configPath(name)
        path.write_text(
            json.dumps(config.toDict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def loadConfig(self, name: str) -> ModelConfig:
        """Load a named model config from disk."""
        path = self._configPath(name)
        if not path.is_file():
            raise ResourceNotFoundError(
                "Configuration de modele introuvable",
                details={"name": name},
            )
        return ModelConfig.fromDict(json.loads(path.read_text(encoding="utf-8")))

    def listConfigs(self) -> list[str]:
        """Return the names of the persisted configs."""
        return sorted(path.stem for path in self._configDir.glob("*.json"))

    def deleteConfig(self, name: str) -> bool:
        """Delete a named config, returning False when it does not exist."""
        path = self._configPath(name)
        if not path.is_file():
            return False
        path.unlink()
        return True

    def _configPath(self, name: str) -> Path:
        """Validate the name and resolve its JSON path inside the config dir."""
        if not _NAME_PATTERN.fullmatch(name):
            raise ValidationError(
                "Nom de configuration invalide",
                details={"name": name},
            )
        path = (self._configDir / f"{name}.json").resolve()
        if not path.is_relative_to(self._configDir.resolve()):
            raise ValidationError(
                "Chemin de configuration hors du repertoire autorise",
                details={"name": name},
            )
        return path
