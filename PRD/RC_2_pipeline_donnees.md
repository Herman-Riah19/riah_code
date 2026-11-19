# RC_2 — Pipeline de Données : Scraping, Nettoyage & Préparation

## 1. Objectifs

Construire un corpus d'entraînement de haute qualité à partir de sources ouvertes :
- **Wikipedia** : Articles complets (FR, EN, autres langues cibles) via API + dumps
- **Plateformes bibliques** : Textes bibliques multi-langues (API Bible Gateway, Bible.com, ou dumps publics)
- **Extensions futures** : Common Crawl, Project Gutenberg, OpenSubtitles, etc.

Sorties attendues :
1. **Corpus brut** : JSONL lignes `{id, source, url, language, text, metadata}`
2. **Corpus nettoyé** : JSONL lignes `{id, source, language, text, qualityScore}`
3. **Shards d'entraînement** : Fichiers `.bin` (memmap uint16) + index `.idx` pour `torch.utils.data.Dataset`

---

## 2. Architecture Pipeline (Classes Pures dans `apps/pipelines/`)

```
apps/pipelines/
├── baseScraper.py          # Classe abstraite Scraper
├── wikiScraper.py          # Wikipedia API + dump parser
├── bibleScraper.py         # Plateformes bibliques (API/HTML)
├── htmlCleaner.py          # Nettoyage HTML → texte brut
├── textNormalizer.py       # Normalisation Unicode, whitespace, contrôles
├── qualityFilter.py        # Filtrage qualité (perplexité, répétitions, langue)
├── deduplicator.py         # Déduplication MinHash + exacte
├── shardWriter.py          # Écriture shards .bin/.idx (memmap)
└── pipelineOrchestrator.py # Orchestration bout-en-bout
```

### 2.1 Interfaces Communes

```python
# apps/models/corpus.py
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

@dataclass(frozen=True)
class RawDocument:
    id: str                    # UUID v4
    source: str                # "wikipedia", "bible_gateway", "common_crawl"
    sourceUrl: str
    language: str              # ISO 639-1 (fr, en, es, de, etc.)
    text: str                  # Texte brut extrait
    metadata: dict             # Spécifique à la source (title, category, book/chapter, etc.)
    scrapedAt: datetime
    contentHash: str           # SHA256 du texte pour déduplication exacte

@dataclass(frozen=True)
class CleanDocument:
    id: str
    source: str
    language: str
    text: str                  # Texte nettoyé, normalisé
    qualityScore: float        # 0.0 - 1.0
    tokenCount: int            # Estimation (approx words * 1.3)
    cleanedAt: datetime

@dataclass(frozen=True)
class ShardInfo:
    shardId: int
    filePath: Path             # .bin file
    indexPath: Path            # .idx file (offsets)
    documentCount: int
    tokenCount: int
    languages: list[str]
```

### 2.2 Scraper Wikipedia (`WikiScraper`)

```python
# apps/pipelines/wikiScraper.py
class WikiScraper(BaseScraper):
    def __init__(
        self,
        languages: list[str] = ["fr", "en"],
        maxArticlesPerLang: int = 100_000,
        useDump: bool = True,           # True = dump Wikimedia, False = API REST
        dumpDate: str = "latest",       # ex: "20241201"
        minArticleLength: int = 500,    # caractères
        excludedNamespaces: list[str] = ["Talk", "User", "Template", "Category", "File"]
    ):
        ...

    def scrape(self, outputDir: Path, corpusRepo: CorpusRepository) -> ScrapeResult:
        """
        1. Si useDump: télécharge dump XML, parse streaming (memory efficient)
        2. Sinon: API REST `action=query&list=allpages&aplimit=500`
        3. Filtre namespaces, longueur min, redirections
        4. Extrait texte (strip mediawiki markup via mwparserfromhell ou regex)
        5. Émet RawDocument via corpusRepo.saveRaw()
        """
        ...

    def _parseDumpStream(self, dumpPath: Path) -> Iterator[RawDocument]:
        # Streaming XML parsing (lxml.iterparse) pour gros dumps
        ...

    def _fetchViaApi(self, language: str) -> Iterator[RawDocument]:
        # Pagination API, rate limiting respectueux
        ...
```

### 2.3 Scraper Biblique (`BibleScraper`)

```python
# apps/pipelines/bibleScraper.py
class BibleScraper(BaseScraper):
    def __init__(
        self,
        source: str = "bible_gateway",  # "bible_gateway", "bible_com", "local_dump"
        languages: list[str] = ["fr", "en", "es", "de", "pt", "it", "zh", "ar"],
        translationsPerLang: dict[str, list[str]] = {
            "fr": ["LSG", "BDS", "NEG"],
            "en": ["KJV", "NIV", "ESV"],
            "es": ["RVR1960", "NVI"],
        },
        includeApocrypha: bool = False,
        versePerDocument: bool = True,      # True = 1 doc/verset, False = 1 doc/chapitre
    ):
        ...

    def scrape(self, outputDir: Path, corpusRepo: CorpusRepository) -> ScrapeResult:
        """
        Selon source:
        - bible_gateway: API non officielle (scraping respectueux + cache)
        - bible_com: API partenaire ou scraping
        - local_dump: fichiers USFX/OSIS/JSON pré-téléchargés
        Émet RawDocument avec metadata: {book, chapter, verse, translation}
        """
        ...
```

### 2.4 Nettoyage HTML (`HtmlCleaner`)

```python
# apps/pipelines/htmlCleaner.py
class HtmlCleaner:
    def __init__(
        self,
        removeTags: list[str] = ["script", "style", "nav", "footer", "header", "aside", "form", "button", "input"],
        keepLinks: bool = False,
        unwrapTags: list[str] = ["div", "span", "section", "article", "main", "p", "br"],
        preserveCode: bool = True,
    ):
        ...

    def clean(self, html: str) -> str:
        """
        1. lxml.html.fromstring
        2. Supprime tags indésirables (scripts, styles, nav, etc.)
        3. Unwrap tags structurels (garde texte, supprime balise)
        4. Convertit <br>, <p> → newlines
        5. text_content() + nettoyage whitespace
        """
        ...
```

### 2.5 Normalisation Texte (`TextNormalizer`)

```python
# apps/pipelines/textNormalizer.py
class TextNormalizer:
    def __init__(
        self,
        unicodeForm: str = "NFC",           # Normalisation Unicode
        fixMojibake: bool = True,           # ftfy pour réparer encodages cassés
        collapseWhitespace: bool = True,    # Multiple spaces/newlines → single
        removeControlChars: bool = True,    # Supprime \x00-\x1f sauf \n\t
        normalizeQuotes: bool = True,       # Guillemets courbes → droits
        normalizeDashes: bool = True,       # Tirets divers → -
        minLineLength: int = 10,            # Ignore lignes trop courtes
    ):
        ...

    def normalize(self, text: str) -> str:
        ...
```

### 2.6 Filtrage Qualité (`QualityFilter`)

```python
# apps/pipelines/qualityFilter.py
class QualityFilter:
    def __init__(
        self,
        minCharLength: int = 100,
        maxCharLength: int = 1_000_000,
        minWordCount: int = 20,
        maxSymbolRatio: float = 0.3,        # Ratio symboles/lettres
        maxRepetitionRatio: float = 0.15,   # n-grammes répétés
        minLanguageScore: float = 0.8,      # fasttext langid score
        targetLanguages: list[str] = ["fr", "en"],
        perplexityThreshold: float | None = None,  # Optionnel: modèle kenlm petit
    ):
        ...

    def filter(self, doc: CleanDocument) -> bool:
        """
        Retourne True si document passe tous les filtres.
        Loggue raison rejet si False.
        """
        ...
```

### 2.7 Déduplication (`Deduplicator`)

```python
# apps/pipelines/deduplicator.py
class Deduplicator:
    def __init__(
        self,
        exactDedup: bool = True,            # Hash SHA256 exact
        minhashDedup: bool = True,          # MinHash LSH pour near-dup
        minhashNumPerm: int = 128,
        minhashThreshold: float = 0.7,      # Jaccard similarity
        ngramSize: int = 5,                 # 5-grammes pour MinHash
        batchSize: int = 100_000,
    ):
        ...

    def deduplicate(self, docs: list[CleanDocument]) -> list[CleanDocument]:
        """
        1. Exact dedup: group by contentHash, keep first
        2. MinHash LSH: datasketch ou implémentation custom
           - Calcule signatures MinHash par doc
           - LSH buckets → candidats near-dup
           - Comparaison Jaccard réelle → suppression
        Retourne liste dédupliquée + stats (removed, kept)
        """
        ...
```

### 2.8 Écriture Shards (`ShardWriter`)

```python
# apps/pipelines/shardWriter.py
class ShardWriter:
    def __init__(
        self,
        outputDir: Path,
        shardSizeTokens: int = 100_000_000,  # ~100M tokens par shard
        dtype: str = "uint16",               # uint16 pour vocab ≤ 65535
        tokenizer: Tokenizer,                # Pour encodage text → IDs
        compression: str = "none",           # "none", "gzip", "zstd"
    ):
        ...

    def writeShards(self, docs: list[CleanDocument]) -> list[ShardInfo]:
        """
        1. Encode chaque doc.text → list[int] via tokenizer
        2. Concatène tous IDs, sépare par token EOS
        3. Découpe en shards de shardSizeTokens
        4. Écrit .bin (np.memmap) + .idx (offsets uint64)
        5. Retourne liste ShardInfo pour index global
        """
        ...

    def _writeShard(self, tokenIds: np.ndarray, shardId: int) -> ShardInfo:
        # np.memmap write, flush, index offsets
        ...
```

### 2.9 Orchestrateur (`PipelineOrchestrator`)

```python
# apps/pipelines/pipelineOrchestrator.py
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
        Étapes séquentielles avec checkpoints intermédiaires:
        1. SCRAPE: Lance tous scrapers → RawDocument (save via repo)
        2. CLEAN: Load raw → HtmlCleaner → TextNormalizer → CleanDocument
        3. FILTER: QualityFilter → CleanDocument filtrés
        4. DEDUP: Deduplicator → CleanDocument uniques
        5. SHARD: ShardWriter → .bin/.idx + ShardInfo
        6. INDEX: Met à jour index global (SQLite/Parquet) pour DataLoader
        
        Chaque étape:
        - Checkpoint automatique (état + position)
        - Reprise possible (--resume-from-step)
        - Logs structurés + métriques (docs in/out, tokens, temps)
        """
        ...
```

---

## 3. Configuration (Pydantic Settings)

```python
# apps/config/dataPipeline.py
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
    languages: list[str] = ["fr", "en", "es", "de", "pt", "it"]
    translationsPerLang: dict[str, list[str]] = {
        "fr": ["LSG", "BDS"],
        "en": ["KJV", "NIV"],
    }
    versePerDocument: bool = True

class PipelineConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PIPELINE_")
    outputDir: Path = Path("data/corpus")
    shardSizeTokens: int = 100_000_000
    tokenizerPath: Path = "tokenizer/tokenizer.json"
    numWorkers: int = 4
    batchSize: int = 1000
    resumeFromStep: str | None = None  # "scrape", "clean", "filter", "dedup", "shard"
```

---

## 4. Repository Corpus (`CorpusRepository`)

```python
# apps/repositories/corpusRepository.py
class CorpusRepository:
    def __init__(self, baseDir: Path):
        self._rawDir = baseDir / "raw"
        self._cleanDir = baseDir / "clean"
        self._shardDir = baseDir / "shards"
        self._indexDb = baseDir / "corpus_index.sqlite"
        self._initDirs()

    def saveRaw(self, docs: list[RawDocument]) -> int:
        # Append JSONL (gzip) par source/date
        ...

    def loadRaw(self, source: str | None = None, limit: int | None = None) -> Iterator[RawDocument]:
        # Streaming load
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
        # Retourne shards selon split (train/val/test)
        ...
```

---

## 5. Service Orchestration (`CorpusService`)

```python
# apps/services/corpusService.py
class CorpusService:
    def __init__(
        self,
        orchestrator: PipelineOrchestrator,
        corpusRepo: CorpusRepository,
        jobRepo: JobRepository,
    ):
        ...

    def startPipeline(self, config: PipelineConfig, userId: str) -> Job:
        job = Job.create(type=JobType.DATA_PIPELINE, config=config, userId=userId)
        self._jobRepo.save(job)
        # Submit to worker pool
        self._workerPool.submit(self._runPipeline, job.id)
        return job

    def _runPipeline(self, jobId: str) -> None:
        job = self._jobRepo.findById(jobId)
        try:
            result = self._orchestrator.runFullPipeline(job.config)
            job.status = JobStatus.COMPLETED
            job.result = result
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
        finally:
            self._jobRepo.save(job)
```

---

## 6. Contrôleur API (`DataController`)

```python
# apps/controllers/dataController.py
dataBlueprint = Blueprint("data", __name__, url_prefix="/api/data")

@dataBlueprint.route("/pipeline/start", methods=["POST"])
@validateInput(PipelineStartRequest)
@requireAuth
def startPipeline(validated: PipelineStartRequest, user: User) -> Response:
    config = PipelineConfig(**validated.model_dump())
    job = corpusService.startPipeline(config, user.id)
    return jsonify(JobResponse.fromJob(job)), 202

@dataBlueprint.route("/pipeline/<jobId>/status", methods=["GET"])
@requireAuth
def getPipelineStatus(jobId: str, user: User) -> Response:
    job = jobRepo.findById(jobId)
    if not job or job.userId != user.id:
        raise ResourceNotFoundError("Job")
    return jsonify(JobStatusResponse.fromJob(job))

@dataBlueprint.route("/corpus/stats", methods=["GET"])
@requireAuth
def getCorpusStats(user: User) -> Response:
    stats = corpusRepo.getGlobalStats()
    return jsonify(CorpusStatsResponse(**stats))
```

---

## 7. Formats de Fichiers

| Fichier | Format | Description |
|---------|--------|-------------|
| `raw/*.jsonl.gz` | JSONL gzippé | Documents bruts (1 ligne = 1 doc) |
| `clean/*.parquet` | Parquet | Documents nettoyés, partitionnés par langue |
| `shards/shard_XXXXXX.bin` | memmap uint16 | Tokens concaténés (EOS entre docs) |
| `shards/shard_XXXXXX.idx` | binary uint64 | Offsets début de chaque document |
| `corpus_index.sqlite` | SQLite | Index global (shard_id, doc_offset, token_count, language) |
| `pipeline_checkpoint_<step>.json` | JSON | État reprise (étape, position, stats) |

---

## 8. Critères d'Acceptation

| Critère | Seuil |
|---------|-------|
| Volume corpus final | ≥ 10 GB texte nettoyé (≈ 3B tokens) |
| Taux déduplication | > 95% documents uniques (exact + near) |
| Qualité langue | > 98% documents dans langues cibles (fasttext) |
| Vitesse scraping | > 1000 docs/min (Wikipedia API) |
| Vitesse nettoyage | > 10 MB/s (HTML → texte) |
| Vitesse encodage | > 50 MB/s (texte → token IDs) |
| Reprise pipeline | Reprend exact à l'étape interrompue |
| Mémoire max | < 4 GB RAM (streaming, pas de chargement full) |

---

## 9. Dépendances Externes

```toml
# pyproject.toml additions
[project.optional-dependencies]
data-pipeline = [
    "lxml>=5.0",
    "mwparserfromhell>=0.6",
    "ftfy>=6.2",
    "fasttext>=0.9.2",           # Pour langid
    "datasketch>=1.6",           # MinHash LSH
    "polars>=1.0",               # Parquet rapide
    "zstandard>=0.22",           # Compression shards
    "tqdm>=4.66",                # Progress bars
    "requests>=2.31",            # HTTP scraping
    "aiohttp>=3.9",              # Async scraping
]
```