# apps/modules/corpus/pipelines/markdownExporter.py
"""Export accepted documents as standalone markdown files for training."""
from __future__ import annotations

import json
import re
from pathlib import Path

from ..models.corpusModel import CleanDocument

FRONT_MATTER_DELIMITER = "---"
UNSAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9_-]")


class MarkdownExporter:
    """Write one `.md` file per clean document with YAML-like front matter."""

    def exportDocument(self, document: CleanDocument, markdownDir: Path) -> Path:
        """Persist a document under `markdownDir/<source>/<language>/<id>.md`."""
        documentDir = markdownDir / document.source / document.language
        documentDir.mkdir(parents=True, exist_ok=True)
        safeId = UNSAFE_FILENAME_PATTERN.sub("_", document.id)
        filePath = documentDir / f"{safeId}.md"
        filePath.write_text(self._render(document), encoding="utf-8")
        return filePath

    def _render(self, document: CleanDocument) -> str:
        frontMatter = {
            "id": document.id,
            "source": document.source,
            "language": document.language,
            "qualityScore": document.qualityScore,
            "tokenCount": document.tokenCount,
            "cleanedAt": document.cleanedAt.isoformat(),
        }
        lines = [
            (
                f"{key}: {json.dumps(value, ensure_ascii=False)}"
                if isinstance(value, str)
                else f"{key}: {value}"
            )
            for key, value in frontMatter.items()
        ]
        return (
            f"{FRONT_MATTER_DELIMITER}\n"
            + "\n".join(lines)
            + f"\n{FRONT_MATTER_DELIMITER}\n\n"
            + document.text
            + "\n"
        )
