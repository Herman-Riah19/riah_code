# tests/unit/test_corpus/test_corpusService.py
"""TDD Tests pour le module corpus - Service - écrits AVANT l'implémentation"""

from pathlib import Path
from unittest.mock import MagicMock

from apps.modules.corpus.models.corpusModel import CorpusStats, PipelineConfig
from apps.modules.corpus.services.corpusService import CorpusService


class TestCorpusService:
    """Tests du service corpus - logique métier"""

    def test_start_pipeline_returns_job_id(self):
        """Démarrage d'un pipeline - doit retourner un ID de job"""
        mock_orchestrator = MagicMock()
        mock_corpus_repo = MagicMock()
        mock_job_repo = MagicMock()
        mock_worker_pool = MagicMock()

        service = CorpusService(
            orchestrator=mock_orchestrator,
            corpusRepo=mock_corpus_repo,
            jobRepo=mock_job_repo,
            workerPool=mock_worker_pool,
        )

        config = PipelineConfig(outputDir=Path("data/corpus"))
        job_id = service.startPipeline(config, userId="user-1")
        assert job_id is not None
        assert isinstance(job_id, str)

    def test_get_stats_returns_corpus_stats(self):
        """Récupération des stats - doit retourner un CorpusStats"""
        mock_orchestrator = MagicMock()
        mock_corpus_repo = MagicMock()
        mock_job_repo = MagicMock()
        mock_worker_pool = MagicMock()

        mock_corpus_repo.getGlobalStats.return_value = CorpusStats(
            totalDocuments=1000,
            totalTokens=50000,
            totalSizeBytes=1024000,
            languages={"fr": 600, "en": 400},
        )

        service = CorpusService(
            orchestrator=mock_orchestrator,
            corpusRepo=mock_corpus_repo,
            jobRepo=mock_job_repo,
            workerPool=mock_worker_pool,
        )

        stats = service.getStats()
        assert stats.totalDocuments == 1000
        assert stats.totalTokens == 50000
        assert "fr" in stats.languages
