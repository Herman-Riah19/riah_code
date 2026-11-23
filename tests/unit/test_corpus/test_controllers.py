# tests/unit/test_corpus/test_controllers.py
"""TDD Tests pour le module corpus - Controller - écrits AVANT l'implémentation"""

from apps.modules.corpus.controllers.corpusController import corpusBlueprint


class TestCorpusController:
    """Tests du controller corpus - routes HTTP"""

    def test_blueprint_exists(self):
        """Le blueprint corpus doit exister"""
        assert corpusBlueprint is not None
        assert corpusBlueprint.name == "corpus"

    def test_blueprint_url_prefix(self):
        """Le préfixe d'URL doit être /api/corpus"""
        assert corpusBlueprint.url_prefix == "/api/corpus"