# tests/unit/test_corpus/test_corpusRepository.py
"""TDD Tests pour le module corpus - Repository - écrits AVANT l'implémentation"""

from pathlib import Path
from apps.modules.corpus.models.corpusModel import (
    RawDocument,
    CleanDocument,
    ShardInfo,
)
from apps.modules.corpus.repositories.corpusRepository import CorpusRepository


class TestCorpusRepository:
    """Tests du repository corpus - CRUD complet"""

    @staticmethod
    def _make_raw_doc(doc_id: str, source: str = "wikipedia", language: str = "fr") -> RawDocument:
        from datetime import datetime
        return RawDocument(
            id=doc_id,
            source=source,
            sourceUrl=f"https://example.com/{doc_id}",
            language=language,
            text=f"Texte du document {doc_id}",
            metadata={},
            scrapedAt=datetime.utcnow(),
        )

    @staticmethod
    def _make_clean_doc(doc_id: str, language: str = "fr") -> CleanDocument:
        from datetime import datetime
        return CleanDocument(
            id=doc_id,
            source="wikipedia",
            language=language,
            text=f"Texte nettoyé {doc_id}",
            qualityScore=0.9,
            tokenCount=5,
            cleanedAt=datetime.utcnow(),
        )

    def test_save_raw_documents(self):
        """Sauvegarde de documents bruts - doit retourner le count"""
        repo = CorpusRepository(baseDir=Path("/tmp/test_corpus_repo"))
        docs = [self._make_raw_doc("doc-1"), self._make_raw_doc("doc-2")]
        count = repo.saveRaw(docs)
        assert count == 2

    def test_load_raw_documents(self):
        """Chargement de documents bruts - doit retourner un itérateur"""
        repo = CorpusRepository(baseDir=Path("/tmp/test_corpus_repo"))
        docs = list(repo.loadRaw())
        assert isinstance(docs, list)

    def test_save_clean_documents(self):
        """Sauvegarde de documents nettoyés - doit retourner le count"""
        repo = CorpusRepository(baseDir=Path("/tmp/test_corpus_repo"))
        docs = [self._make_clean_doc("doc-1"), self._make_clean_doc("doc-2")]
        count = repo.saveClean(docs)
        assert count == 2

    def test_load_clean_documents(self):
        """Chargement de documents nettoyés - doit retourner un itérateur"""
        repo = CorpusRepository(baseDir=Path("/tmp/test_corpus_repo"))
        docs = list(repo.loadClean())
        assert isinstance(docs, list)

    def test_save_shard_info(self):
        """Sauvegarde d'informations de shard - ne doit pas lever d'erreur"""
        repo = CorpusRepository(baseDir=Path("/tmp/test_corpus_repo"))
        shards = [
            ShardInfo(
                shardId=1,
                filePath=Path("shard_000001.bin"),
                indexPath=Path("shard_000001.idx"),
                documentCount=100,
                tokenCount=5000,
                languages=["fr"],
            )
        ]
        repo.saveShardInfo(shards)  # Ne doit pas lever d'exception

    def test_get_shards_for_training(self):
        """Récupération des shards pour l'entraînement - doit retourner une liste"""
        repo = CorpusRepository(baseDir=Path("/tmp/test_corpus_repo"))
        shards = repo.getShardsForTraining(split="train")
        assert isinstance(shards, list)