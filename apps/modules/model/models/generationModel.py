"""Generation options and request validation models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class GenerationOptions:
    """Sampling parameters for text generation."""

    maxTokens: int = 128
    temperature: float = 0.7
    topK: int | None = 50
    topP: float = 0.9
    repetitionPenalty: float = 1.1
    stopSequences: list[str] = field(default_factory=list)
    seed: int | None = None

    def toDict(self) -> dict[str, Any]:
        """Serialize to camelCase primitives."""
        return {
            "maxTokens": self.maxTokens,
            "temperature": self.temperature,
            "topK": self.topK,
            "topP": self.topP,
            "repetitionPenalty": self.repetitionPenalty,
            "stopSequences": list(self.stopSequences),
            "seed": self.seed,
        }


class GenerateRequest(BaseModel):
    """HTTP payload used to generate text from a checkpoint."""

    prompt: str = Field(min_length=1, max_length=100_000)
    checkpointId: str | None = None
    maxTokens: int = Field(default=128, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=5.0)
    topK: int | None = Field(default=50, ge=0, le=100_000)
    topP: float = Field(default=0.9, gt=0.0, le=1.0)
    repetitionPenalty: float = Field(default=1.1, gt=0.0, le=10.0)
    stopSequences: list[str] = Field(default_factory=list, max_length=16)
    seed: int | None = None

    def toOptions(self) -> GenerationOptions:
        """Convert the validated request into generation options."""
        return GenerationOptions(
            maxTokens=self.maxTokens,
            temperature=self.temperature,
            topK=self.topK,
            topP=self.topP,
            repetitionPenalty=self.repetitionPenalty,
            stopSequences=list(self.stopSequences),
            seed=self.seed,
        )


__all__ = ["GenerateRequest", "GenerationOptions"]
