# tests/unit/test_corpus/test_pipelineOrchestrator.py
"""TDD Tests pour le module corpus - Pipeline Orchestrator - écrits AVANT l'implémentation"""

from pathlib import Path
from apps.modules.corpus.models.corpusModel import PipelineConfig
from apps.modules.corpus.pipelines.pipelineOrchestrator import PipelineOrchestrator


class TestPipelineOrchestrator:
    """Tests de l'orchestrateur de pipeline"""

    def test_run_full_pipeline_returns_result(self):
        """Exécution complète du pipeline - doit retourner un résultat"""
        from unittest.mock import MagicMock
        mock_scrapers = [MagicMock(), MagicMock()]
        mock_cleaner = MagicMock()
        mock_normalizer = MagicMock()
        mock_quality_filter = MagicMock()
        mock_deduplicator = MagicMock()
        mock_shard_writer = MagicMock()
        mock_corpus_repo = MagicMock()

        orchestrator = PipelineOrchestrator(
            scrapers=mock_scrapers,
            cleaner=mock_cleaner,
            normalizer=mock_normalizer,
            qualityFilter=mock_quality_filter,
            deduplicator=mock_deduplicator,
            shardWriter=mock_shard_writer,
            corpusRepo=mock_corpus_repo,
            checkpointDir=Path("/tmp/test_checkpoints"),
        )

        config = PipelineConfig(outputDir=Path("data/corpus"))
        result = orchestrator.runFullPipeline(config)
        assert result is not None