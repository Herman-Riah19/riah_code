# Architecture DDD — Structure des Modules (Bounded Contexts)

Chaque domaine métier est un **module indépendant** sous `apps/modules/` avec sa propre structure interne :

```
apps/modules/
├── corpus/                    # Domaine : Corpus de données
│   ├── models/                # Entités de domaine
│   │   ├── corpusModel.py     # RawDocument, CleanDocument, ShardInfo
│   │   └── __init__.py
│   ├── repositories/          # Accès données
│   │   ├── corpusRepository.py
│   │   └── __init__.py
│   ├── services/              # Logique métier
│   │   ├── corpusService.py
│   │   └── __init__.py
│   ├── pipelines/             # Pipelines de traitement (classes pures)
│   │   ├── wikiScraper.py
│   │   ├── bibleScraper.py
│   │   ├── htmlCleaner.py
│   │   ├── textNormalizer.py
│   │   ├── qualityFilter.py
│   │   ├── deduplicator.py
│   │   ├── shardWriter.py
│   │   ├── pipelineOrchestrator.py
│   │   └── __init__.py
│   ├── controllers/           # API HTTP
│   │   ├── corpusController.py
│   │   └── __init__.py
│   └── __init__.py            # Exports publics du module
│
├── tokenizer/                 # Domaine : Tokenizer BPE
│   ├── models/
│   │   ├── tokenizerModel.py  # TokenizerConfig, VocabInfo, BPETokenizer
│   │   └── __init__.py
│   ├── repositories/
│   │   ├── tokenizerRepository.py
│   │   └── __init__.py
│   ├── services/
│   │   ├── tokenizerService.py
│   │   └── __init__.py
│   ├── pipelines/
│   │   ├── tokenizerTrainer.py
│   │   ├── corpusEncoder.py
│   │   └── __init__.py
│   ├── controllers/
│   │   ├── tokenizerController.py
│   │   └── __init__.py
│   └── __init__.py
│
├── model/                     # Domaine : Modèle Transformer
│   ├── models/
│   │   ├── modelModel.py      # ModelConfig, ModelPresets
│   │   └── __init__.py
│   ├── repositories/
│   │   ├── modelRepository.py     # Pour configs/presets
│   │   ├── checkpointRepository.py # Pour checkpoints entraînement
│   │   └── __init__.py
│   ├── services/
│   │   ├── trainingService.py
│   │   ├── inferenceService.py
│   │   └── __init__.py
│   ├── ml/                    # Composants ML purs (réutilisables)
│   │   ├── transformer.py
│   │   ├── attention.py
│   │   ├── feedForward.py
│   │   ├── embedding.py
│   │   ├── normalization.py
│   │   ├── loss.py
│   │   ├── sampler.py
│   │   ├── modelRunner.py
│   │   └── __init__.py
│   ├── pipelines/
│   │   ├── trainingLoop.py
│   │   ├── shardedDataset.py
│   │   └── __init__.py
│   ├── controllers/
│   │   ├── trainingController.py
│   │   ├── inferenceController.py
│   │   └── __init__.py
│   └── __init__.py
│
├── chat/                      # Domaine : Chat / Inférence interactive
│   ├── models/
│   │   ├── chatModel.py       # ChatSession, ChatMessage, GenerationOptions
│   │   └── __init__.py
│   ├── repositories/
│   │   ├── chatRepository.py  # Historique conversations
│   │   └── __init__.py
│   ├── services/
│   │   ├── chatService.py
│   │   └── __init__.py
│   ├── controllers/
│   │   ├── chatController.py  # REST + WebSocket
│   │   └── __init__.py
│   └── __init__.py
│
├── shared/                    # Kernel partagé (cross-cutting)
│   ├── decorators/
│   │   ├── auth.py
│   │   ├── validation.py
│   │   ├── retry.py
│   │   ├── logging.py
│   │   ├── rateLimit.py
│   │   └── __init__.py
│   ├── kernel/
│   │   ├── events.py          # Domain events
│   │   ├── exceptions.py      # RiahAppError hierarchy
│   │   ├── valueObjects.py    # Value objects communs
│   │   └── __init__.py
│   ├── storage/
│   │   ├── fileStorage.py
│   │   ├── sqliteStorage.py
│   │   ├── s3Storage.py
│   │   └── __init__.py
│   └── config.py              # Pydantic Settings global
│
└── __init__.py                # Module racine
```

---

## Règles de Nommage par Module

| Module | Modèles | Repository | Service | Pipeline | Controller | ML/Core |
|--------|---------|------------|---------|----------|------------|---------|
| **corpus** | `corpusModel.py` | `corpusRepository.py` | `corpusService.py` | `*Scraper.py`, `*Cleaner.py`, `pipelineOrchestrator.py` | `corpusController.py` | — |
| **tokenizer** | `tokenizerModel.py` | `tokenizerRepository.py` | `tokenizerService.py` | `tokenizerTrainer.py`, `corpusEncoder.py` | `tokenizerController.py` | — |
| **model** | `modelModel.py` | `modelRepository.py`, `checkpointRepository.py` | `trainingService.py`, `inferenceService.py` | `trainingLoop.py`, `shardedDataset.py` | `trainingController.py`, `inferenceController.py` | `transformer.py`, `attention.py`, `sampler.py`, `modelRunner.py` |
| **chat** | `chatModel.py` | `chatRepository.py` | `chatService.py` | — | `chatController.py` | — |

---

## Exemple : Module Tokenizer (Structure Complète)

```
apps/modules/tokenizer/
├── __init__.py                    # from .models import *; from .services import *
├── models/
│   ├── __init__.py
│   └── tokenizerModel.py          # TokenizerConfig, VocabInfo, BPETokenizer
├── repositories/
│   ├── __init__.py
│   └── tokenizerRepository.py     # save(), load(), exists()
├── services/
│   ├── __init__.py
│   └── tokenizerService.py        # trainTokenizer(), encodeFullCorpus()
├── pipelines/
│   ├── __init__.py
│   ├── tokenizerTrainer.py        # TokenizerTrainer class
│   └── corpusEncoder.py           # CorpusEncoder class
└── controllers/
    ├── __init__.py
    └── tokenizerController.py     # Blueprint Flask routes
```

### `tokenizerModel.py` — Entités du domaine Tokenizer

```python
# apps/modules/tokenizer/models/tokenizerModel.py
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from tokenizers import Tokenizer as HFTokenizer

@dataclass(frozen=True)
class TokenizerConfig:
    vocabSize: int = 32_000
    minFrequency: int = 2
    specialTokens: list[str] = field(default_factory=lambda: [
        "<|endoftext|>", "<|pad|>", "<|unk|>", "<|mask|>"
    ])
    byteFallback: bool = True
    addPrefixSpace: bool = True
    trimWhitespace: bool = False
    showProgress: bool = True
    numThreads: int = 4

@dataclass(frozen=True)
class VocabInfo:
    vocabSize: int
    specialTokenIds: dict[str, int]
    compressionRatio: float
    oovRate: float
    trainedAt: datetime
    configHash: str

class BPETokenizer:
    """Wrapper runtime pour tokenizer entraîné (encode/decode/batch)."""
    
    def __init__(self, tokenizerPath: Path):
        self._hfTokenizer = HFTokenizer.from_file(str(tokenizerPath))
        self._vocab = self._hfTokenizer.get_vocab()
        self._idToToken = {v: k for k, v in self._vocab.items()}
        self._eosId = self._vocab["<|endoftext|>"]
        self._padId = self._vocab["<|pad|>"]
        self._unkId = self._vocab["<|unk|>"]
    
    @property
    def vocabSize(self) -> int:
        return len(self._vocab)
    
    @property
    def eosTokenId(self) -> int:
        return self._eosId
    
    @property
    def padTokenId(self) -> int:
        return self._padId
    
    def encode(self, text: str, addSpecialTokens: bool = True) -> list[int]:
        ids = self._hfTokenizer.encode(text).ids
        if addSpecialTokens:
            ids = ids + [self._eosId]
        return ids
    
    def encodeBatch(self, texts: list[str], addSpecialTokens: bool = True, 
                    padding: bool = True, maxLength: int | None = None) -> dict:
        encodings = self._hfTokenizer.encode_batch(texts, add_special_tokens=addSpecialTokens)
        ids = [e.ids for e in encodings]
        
        if maxLength:
            ids = [seq[:maxLength] for seq in ids]
        
        if padding:
            maxLen = max(len(seq) for seq in ids)
            ids = [seq + [self._padId] * (maxLen - len(seq)) for seq in ids]
            attentionMask = [[1] * len(seq) + [0] * (maxLen - len(seq)) for seq in encodings]
        else:
            attentionMask = [[1] * len(seq) for seq in ids]
        
        return {"inputIds": ids, "attentionMask": attentionMask}
    
    def decode(self, ids: list[int], skipSpecialTokens: bool = True) -> str:
        if skipSpecialTokens:
            ids = [i for i in ids if i not in (self._eosId, self._padId, self._unkId)]
        return self._hfTokenizer.decode(ids)
    
    def decodeBatch(self, idsList: list[list[int]], skipSpecialTokens: bool = True) -> list[str]:
        return [self.decode(ids, skipSpecialTokens) for ids in idsList]
    
    def tokenToId(self, token: str) -> int | None:
        return self._vocab.get(token)
    
    def idToToken(self, id: int) -> str | None:
        return self._idToToken.get(id)
```

### `tokenizerRepository.py` — Persistance

```python
# apps/modules/tokenizer/repositories/tokenizerRepository.py
class TokenizerRepository:
    def __init__(self, baseDir: Path):
        self._baseDir = baseDir
        self._tokenizerPath = baseDir / "tokenizer.json"
        self._vocabInfoPath = baseDir / "vocab_info.json"
    
    def save(self, hfTokenizer: HFTokenizer, vocabInfo: VocabInfo) -> None:
        hfTokenizer.save(str(self._tokenizerPath))
        self._vocabInfoPath.write_text(vocabInfo.to_json())
    
    def load(self) -> tuple[BPETokenizer, VocabInfo]:
        tokenizer = BPETokenizer(self._tokenizerPath)
        vocabInfo = VocabInfo.from_json(self._vocabInfoPath.read_text())
        return tokenizer, vocabInfo
    
    def exists(self) -> bool:
        return self._tokenizerPath.exists()
```

### `tokenizerService.py` — Orchestration Métier

```python
# apps/modules/tokenizer/services/tokenizerService.py
class TokenizerService:
    def __init__(
        self,
        trainer: TokenizerTrainer,
        encoder: CorpusEncoder,
        tokenizerRepo: TokenizerRepository,
        corpusRepo: CorpusRepository,  # Dépendance cross-module via interface
        jobRepo: JobRepository,
    ):
        ...
    
    def trainTokenizer(self, config: TokenizerConfig, corpusSampleSize: int = 10_000_000) -> VocabInfo:
        sampleIter = self._corpusRepo.sampleClean(corpusSampleSize)
        vocabInfo = self._trainer.train(sampleIter)
        self._tokenizerRepo.save(self._trainer._hfTokenizer, vocabInfo)
        return vocabInfo
    
    def encodeFullCorpus(self, tokenizerPath: Path) -> EncodedCorpusStats:
        tokenizer = BPETokenizer(tokenizerPath)
        encoder = CorpusEncoder(tokenizer, self._corpusRepo.shardDir)
        docsIter = self._corpusRepo.loadClean()
        return encoder.encodeCorpus(docsIter)
```

---

## Dépendances Inter-Modules (Règles)

```
corpus        → shared (storage, kernel, config)
tokenizer     → shared + corpus (via CorpusRepository interface)
model         → shared + tokenizer (via TokenizerRepository interface)
chat          → shared + model (via InferenceService interface)
```

**Règle** : Un module n'importe **jamais** l'implémentation concrète d'un autre module. Il dépend uniquement des **interfaces** (Repository, Service) définies dans le module cible.

```python
# CORRECT - model/service/trainingService.py
from apps.modules.tokenizer.repositories.tokenizerRepository import TokenizerRepository
from apps.modules.corpus.repositories.corpusRepository import CorpusRepository

class TrainingService:
    def __init__(self, tokenizerRepo: TokenizerRepository, corpusRepo: CorpusRepository):
        ...

# INTERDIT
from apps.modules.tokenizer.pipelines.tokenizerTrainer import TokenizerTrainer  # Implémentation concrète
```

---

## Factory d'Application (Composition Root)

```python
# apps/__init__.py
from flask import Flask
from apps.modules.corpus.repositories.corpusRepository import CorpusRepository
from apps.modules.tokenizer.repositories.tokenizerRepository import TokenizerRepository
from apps.modules.model.repositories.checkpointRepository import CheckpointRepository
from apps.modules.chat.repositories.chatRepository import ChatRepository
from apps.modules.corpus.services.corpusService import CorpusService
from apps.modules.tokenizer.services.tokenizerService import TokenizerService
from apps.modules.model.services.trainingService import TrainingService
from apps.modules.model.services.inferenceService import InferenceService
from apps.modules.chat.services.chatService import ChatService
from apps.shared.config import Settings

def createApp(config: Settings | None = None) -> Flask:
    app = Flask(__name__)
    config = config or Settings()
    app.config.from_object(config)
    
    # Repositories (infrastructure)
    corpusRepo = CorpusRepository(config.dataDir / "corpus")
    tokenizerRepo = TokenizerRepository(config.dataDir / "tokenizer")
    checkpointRepo = CheckpointRepository(config.dataDir / "checkpoints")
    chatRepo = ChatRepository(config.dataDir / "chat")
    
    # Services (domain logic)
    corpusService = CorpusService(corpusRepo, config)
    tokenizerService = TokenizerService(tokenizerRepo, corpusRepo, config)
    trainingService = TrainingService(tokenizerRepo, checkpointRepo, corpusRepo, config)
    inferenceService = InferenceService(tokenizerRepo, checkpointRepo, config)
    chatService = ChatService(inferenceService, chatRepo, config)
    
    # Controllers (HTTP)
    from apps.modules.corpus.controllers.corpusController import corpusBlueprint
    from apps.modules.tokenizer.controllers.tokenizerController import tokenizerBlueprint
    from apps.modules.model.controllers.trainingController import trainingBlueprint
    from apps.modules.model.controllers.inferenceController import inferenceBlueprint
    from apps.modules.chat.controllers.chatController import chatBlueprint
    
    app.register_blueprint(corpusBlueprint)
    app.register_blueprint(tokenizerBlueprint)
    app.register_blueprint(trainingBlueprint)
    app.register_blueprint(inferenceBlueprint)
    app.register_blueprint(chatBlueprint)
    
    # Health check
    @app.route("/health")
    def health():
        return {"status": "ok", "version": config.appVersion}
    
    return app
```

---

## Mise à Jour des PRD Suivants

Tous les PRD (RC_2 à RC_7) doivent être réécrits pour refléter cette structure DDD. Chaque PRD décrit maintenant un **module complet** avec ses modèles, repositories, services, pipelines, controllers.

| PRD | Module | Fichier |
|-----|--------|---------|
| RC_1 | Architecture globale | `RC_1_architecture_globale.md` |
| RC_2 | `corpus` | `RC_2_module_corpus.md` |
| RC_3 | `tokenizer` | `RC_3_module_tokenizer.md` |
| RC_4 | `model` | `RC_4_module_model.md` |
| RC_5 | `chat` + API inference | `RC_5_module_chat_inference.md` |
| RC_6 | Déploiement, migration, monitoring | `RC_6_deploiement_monitoring.md` |
| RC_7 | Tests, qualité, acceptation | `RC_7_tests_qualite.md` |