# RC_2 — Module Corpus : Scraping, Nettoyage & Préparation

## 1. Objectifs

Module **`corpus`** : Construire un corpus d'entraînement de haute qualité depuis sources ouvertes (Wikipedia, Bible, etc.) avec pipelines reproductibles et traçables.

**Sorties** :
- `RawDocument` → JSONL brut (stockage immuable)
- `CleanDocument` → Parquet nettoyé, partitionné
- `ShardInfo` → Shards `.bin/.idx` (memmap uint16) + index SQLite

---

## 2. Structure Module `corpus`

```
apps/modules/corpus/
├── __init__.py
├── models/
│   ├── __init__.py
│   └── corpusModel.py           # RawDocument, CleanDocument, ShardInfo, PipelineConfig
├── repositories/
│   ├── __init__.py
│   └── corpusRepository.py      # saveRaw, loadRaw, saveClean, loadClean, saveShardInfo, getShardsForTraining
├── services/
│   ├── __init__.py
│   └── corpusService.py         # startPipeline, getStats, resumePipeline
├── pipelines/
│   ├── __init__.py
│   ├── baseScraper.py           # AbstractScraper
│   ├── wikiScraper.py           # WikiScraper
│   ├── bibleScraper.py          # BibleScraper
│   ├── htmlCleaner.py           # HtmlCleaner
│   ├── textNormalizer.py        # TextNormalizer
│   ├── qualityFilter.py         # QualityFilter
│   ├── deduplicator.py          # Deduplicator (exact + MinHash)
│   ├── shardWriter.py           # ShardWriter
│   └── pipelineOrchestrator.py  # PipelineOrchestrator
└── controllers/
    ├── __init__.py
    └── corpusController.py      # Blueprint /api/corpus
```

---

## 3. Modèles de Domaine (`corpusModel.py`)

```python
# apps/modules/corpus/models/corpusModel.py
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import hashlib

@dataclass(frozen=True)
class RawDocument:
    id: str
    source: str                    # "wikipedia", "bible_gateway", "common_crawl"
    sourceUrl: str
    language: str                  # ISO 639-1
    text: str
    metadata: dict
    scrapedAt: datetime
    contentHash: str               # SHA256(text)
    
    @classmethod
    def create(cls, source: str, url: str, language: str, text: str, metadata: dict) -> "RawDocument":
        contentHash = hashlib.sha256(text.encode()).hexdigest()
        return cls(
            id=str(uuid.uuid4()),
            source=source,
            sourceUrl=url,
            language=language,
            text=text,
            metadata=metadata,
            scrapedAt=datetime.utcnow(),
            contentHash=contentHash
        )

@dataclass(frozen=True)
class CleanDocument:
    id: str
    source: str
    language: str
    text: str
    qualityScore: float            # 0.0 - 1.0
    tokenCount: int
    cleanedAt: datetime

@dataclass(frozen=True)
class ShardInfo:
    shardId: int
    filePath: Path
    indexPath: Path
    documentCount: int
    tokenCount: int
    languages: list[str]

@dataclass(frozen=True)
class PipelineConfig:
    outputDir: Path
    shardSizeTokens: int = 100_000_000
    tokenizerPath: Path
    numWorkers: int = 4
    batchSize: int = 1000
    resumeFromStep: str | None = None
    wiki: WikiScraperConfig = field(default_factory=WikiScraperConfig)
    bible: BibleScraperConfig = field(default_factory=BibleScraperConfig)
    cleaner: HtmlCleanerConfig = field(default_factory=HtmlCleanerConfig)
    normalizer: TextNormalizerConfig = field(default_factory=TextNormalizerConfig)
    quality: QualityFilterConfig = field(default_factory=QualityFilterConfig)
    dedup: DeduplicatorConfig = field(default_factory=DeduplicatorConfig)

@dataclass(frozen=True)
class ScrapeResult:
    documentsScraped: int
    documentsSaved: int
    errors: list[str]
    durationSeconds: float
```

---

## 4. Repository (`corpusRepository.py`)

```python
# apps/modules/corpus/repositories/corpusRepository.py
class CorpusRepository:
    def __init__(self, baseDir: Path):
        self._baseDir = baseDir
        self._rawDir = baseDir / "raw"
        self._cleanDir = baseDir / "clean"
        self._shardDir = baseDir / "shards"
        self._indexDb = baseDir / "corpus_index.sqlite"
        self._initDirs()
    
    def saveRaw(self, docs: list[RawDocument]) -> int:
        # Append JSONL gzippé par source/date
        ...
    
    def loadRaw(self, source: str | None = None, limit: int | None = None) -> Iterator[RawDocument]:
        # Streaming load
        ...
    
    def sampleClean(self, sampleSize: int, languages: list[str] | None = None) -> Iterator[CleanDocument]:
        # Reservoir sampling pour entraînement tokenizer
        ...
    
    def saveClean(self, docs: list[CleanDocument]) -> int:
        # Parquet partitionné par langue/source
        ...
    
    def loadClean(self, languages: list[str] | None = None) -> Iterator[CleanDocument]:
        ...
    
    def saveShardInfo(self, shards: list[ShardInfo]) -> None:
        # SQLite table shards + index global
        ...
    
    def getShardsForTraining(self, split: str = "train") -> list[ShardInfo]:
        ...
    
    def getGlobalStats(self) -> CorpusStats:
        ...
```

---

## 5. Pipelines (Classes Pures)

### `baseScraper.py`
```python
# apps/modules/corpus/pipelines/baseScraper.py
from abc import ABC, abstractmethod

class ScrapeResult:
    documentsScraped: int
    documentsSaved: int
    errors: list[str]

class BaseScraper(ABC):
    @abstractmethod
    def scrape(self, outputDir: Path, corpusRepo: CorpusRepository) -> ScrapeResult:
        pass
```

### `wikiScraper.py`
```python
# apps/modules/corpus/pipelines/wikiScraper.py
class WikiScraper(BaseScraper):
    def __init__(self, config: WikiScraperConfig):
        ...
    
    def scrape(self, outputDir: Path, corpusRepo: CorpusRepository) -> ScrapeResult:
        if self.config.useDump:
            return self._scrapeFromDump(corpusRepo)
        return self._scrapeFromApi(corpusRepo)
    
    def _scrapeFromDump(self, corpusRepo: CorpusRepository) -> ScrapeResult:
        # Streaming XML parsing (lxml.iterparse)
        # Filtre namespaces, longueur, redirections
        # Extrait texte (mwparserfromhell)
        # Émet RawDocument via corpusRepo.saveRaw()
        ...
    
    def _scrapeFromApi(self, corpusRepo: CorpusRepository) -> ScrapeResult:
        # Pagination API REST, rate limiting
        ...
```

### `bibleScraper.py`
```python
# apps/modules/corpus/pipelines/bibleScraper.py
class BibleScraper(BaseScraper):
    def __init__(self, config: BibleScraperConfig):
        ...
    
    def scrape(self, outputDir: Path, corpusRepo: CorpusRepository) -> ScrapeResult:
        # Selon source: bible_gateway, bible_com, local_dump
        # Émet RawDocument avec metadata: {book, chapter, verse, translation}
        ...
```

### `htmlCleaner.py`, `textNormalizer.py`, `qualityFilter.py`, `deduplicator.py`, `shardWriter.py`
(voir versions détaillées dans RC_2 original — même logique, adaptée aux modèles DDD)

### `pipelineOrchestrator.py`
```python
# apps/modules/corpus/pipelines/pipelineOrchestrator.py
class PipelineOrchestrator:
    def __init__(
        self,
        scrapers: list[BaseScraper],
        cleaner: HtmlCleaner,
        normalizer: TextNormalizer,
        qualityFilter: QualityFilter,
        deduplicator: Deduplicator,
        shardWriter: ShardWriter,
        corpusRepo: CorpusRepository,
        checkpointDir: Path,
    ):
        ...
    
    def runFullPipeline(self, config: PipelineConfig) -> PipelineResult:
        """
        Étapes avec checkpoints:
        1. SCRAPE → RawDocument
        2. CLEAN → CleanDocument (HtmlCleaner + TextNormalizer)
        3. FILTER → QualityFilter
        4. DEDUP → Deduplicator (exact + MinHash)
        5. SHARD → ShardWriter (.bin/.idx)
        6. INDEX → Mise à jour index global
        """
        ...
```

---

## 6. Service (`corpusService.py`)

```python
# apps/modules/corpus/services/corpusService.py
class CorpusService:
    def __init__(
        self,
        orchestrator: PipelineOrchestrator,
        corpusRepo: CorpusRepository,
        jobRepo: JobRepository,
        workerPool: WorkerPool,
    ):
        ...
    
    def startPipeline(self, config: PipelineConfig, userId: str) -> Job:
        job = Job.create(type=JobType.DATA_PIPELINE, config=config, userId=userId)
        self._jobRepo.save(job)
        self._workerPool.submit(self._runPipeline, job.id)
        return job
    
    def resumePipeline(self, jobId: str) -> Job:
        job = self._jobRepo.findById(jobId)
        job.status = JobStatus.PENDING
        self._jobRepo.save(job)
        self._workerPool.submit(self._runPipeline, job.id)
        return job
    
    def getCorpusStats(self) -> CorpusStatsResponse:
        return self._corpusRepo.getGlobalStats()
```

---

## 7. Controller (`corpusController.py`)

```python
# apps/modules/corpus/controllers/corpusController.py
from flask import Blueprint, jsonify
from apps.shared.decorators.auth import requireAuth
from apps.shared.decorators.validation import validateInput

corpusBlueprint = Blueprint("corpus", __name__, url_prefix="/api/corpus")

@corpusBlueprint.route("/pipeline/start", methods=["POST"])
@requireAuth
@validateInput(PipelineStartRequest)
def startPipeline(validated: PipelineStartRequest, user: User):
    config = PipelineConfig(**validated.model_dump())
    job = corpusService.startPipeline(config, user.id)
    return jsonify(JobResponse.fromJob(job)), 202

@corpusBlueprint.route("/pipeline/<jobId>/status", methods=["GET"])
@requireAuth
def getPipelineStatus(jobId: str, user: User):
    job = jobRepo.findById(jobId)
    if not job or job.userId != user.id:
        raise ResourceNotFoundError("Job")
    return jsonify(JobStatusResponse.fromJob(job))

@corpusBlueprint.route("/pipeline/<jobId>/resume", methods=["POST"])
@requireAuth
def resumePipeline(jobId: str, user: User):
    job = corpusService.resumePipeline(jobId)
    return jsonify(JobResponse.fromJob(job))

@corpusBlueprint.route("/stats", methods=["GET"])
@requireAuth
def getCorpusStats(user: User):
    return jsonify(corpusService.getCorpusStats())
```

---

## 8. Configuration (Pydantic Settings)

```python
# apps/modules/corpus/models/corpusModel.py (configs)
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class WikiScraperConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WIKI_")
    languages: list[str] = ["fr", "en"]
    maxArticlesPerLang: int = 100_000
    useDump: bool = True
    dumpDate: str = "latest"
    minArticleLength: int = 500

class BibleScraperConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BIBLE_")
    source: str = "bible_gateway"
    languages: list[str] = ["fr", "en", "es", "de"]
    translationsPerLang: dict[str, list[str]] = {"fr": ["LSG"], "en": ["KJV"]}
    versePerDocument: bool = True

# ... HtmlCleanerConfig, TextNormalizerConfig, QualityFilterConfig, DeduplicatorConfig
```

---

## 9. Critères d'Acceptation

| Critère | Seuil |
|---------|-------|
| Volume corpus final | ≥ 10 GB texte nettoyé (≈ 3B tokens) |
| Taux déduplication | > 95% uniques (exact + near) |
| Qualité langue | > 98% docs langues cibles |
| Vitesse scraping | > 1000 docs/min (Wikipedia API) |
| Vitesse nettoyage | > 10 MB/s |
| Vitesse encodage | > 50 MB/s (texte → token IDs) |
| Reprise pipeline | Reprend exact à l'étape interrompue |
| Mémoire max | < 4 GB RAM (streaming) |