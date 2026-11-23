# tests/unit/test_corpus/test_pipelines.py
"""TDD Tests pour le module corpus - Pipelines - écrits AVANT l'implémentation"""

from pathlib import Path
from apps.modules.corpus.pipelines.baseScraper import BaseScraper, ScrapeResult


class TestPipelines:
    """Tests des classes de pipeline"""

    def test_base_scraper_is_abstract(self):
        """BaseScraper ne doit pas pouvoir être instancié directement"""
        try:
            BaseScraper()
            assert False, "Devrait lever TypeError (classe abstraite)"
        except TypeError:
            pass  # Comportement attendu

    def test_scrape_result_has_fields(self):
        """ScrapeResult doit avoir les champs attendus"""
        result = ScrapeResult()
        assert hasattr(result, "documentsScraped")
        assert hasattr(result, "documentsSaved")
        assert hasattr(result, "errors")
        assert hasattr(result, "durationSeconds")