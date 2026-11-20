# RC_3 — Module Tokenizer : BPE Training & Corpus Encoding

## 1. Objectifs

Module **`tokenizer`** : Entraîner un tokenizer BPE sur le corpus nettoyé, l'encapsuler dans un modèle de domaine `BPETokenizer`, et encoder tout le corpus en shards `.bin/.idx` pour l'entraînement.

**Sorties** :
- `tokenizer.json` (format Hugging Face tokenizers)
- `vocab_info.json` (métadonnées: vocabSize, compressionRatio, OOV rate)
- Shards encodés + index SQLite mis à jour

---

## 2. Structure Module `tokenizer`

```
apps/modules/tokenizer/
├── __init__.py
├── models/
│   ├── __init__.py
│   └── tokenizerModel.py        # TokenizerConfig, VocabInfo, BPETokenizer, EncodedCorpusStats
├── repositories/
│   ├── __init__.py
│   └── tokenizerRepository.py   # save, load, exists
├── services/
│   ├── __init__.py
│   └── tokenizerService.py      # trainTokenizer, encodeFullCorpus
├── pipelines/
│   ├── __init__.py
│   ├── tokenizerTrainer.py      # TokenizerTrainer
│   └── corpusEncoder.py         # CorpusEncoder
└── controllers/
    ├── __init__.py
    └── tokenizerController.py   # Blueprint /api/tokenizer
```

---

## 3. Modèles de Domaine (`tokenizerModel.py`)

```python
# apps/modules/tokenizer/models/tokenizerModel.py
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from tokenizers import Tokenizer as HFTokenizer
import numpy as np

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
    
    def to_json(self) -> str:
        import json
        return json.dumps({
            "vocabSize": self.vocabSize,
            "specialTokenIds": self.specialTokenIds,
            "compressionRatio": self.compressionRatio,
            "oovRate": self.oovRate,
            "trainedAt": self.trainedAt.isoformat(),
            "configHash": self.configHash,
        })
    
    @classmethod
    def from_json(cls, jsonStr: str) -> "VocabInfo":
        import json
        data = json.loads(jsonStr)
        data["trainedAt"] = datetime.fromisoformat(data["trainedAt"])
        return cls(**data)

class BPETokenizer:
    """Wrapper runtime pour tokenizer entraîné — encode/decode/batch."""
    
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
    
    @property
    def unkTokenId(self) -> int:
        return self._unkId
    
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

@dataclass(frozen=True)
class EncodedCorpusStats:
    totalTokens: int
    totalDocuments: int
    shardCount: int
    avgTokensPerDoc: float
    languageDistribution: dict[str, int]
```

---

## 4. Repository (`tokenizerRepository.py`)

```python
# apps/modules/tokenizer/repositories/tokenizerRepository.py
class TokenizerRepository:
    def __init__(self, baseDir: Path):
        self._baseDir = baseDir
        self._tokenizerPath = baseDir / "tokenizer.json"
        self._vocabInfoPath = baseDir / "vocab_info.json"
    
    def save(self, hfTokenizer: HFTokenizer, vocabInfo: VocabInfo) -> None:
        self._baseDir.mkdir(parents=True, exist_ok=True)
        hfTokenizer.save(str(self._tokenizerPath))
        self._vocabInfoPath.write_text(vocabInfo.to_json())
    
    def load(self) -> tuple[BPETokenizer, VocabInfo]:
        if not self._tokenizerPath.exists():
            raise TokenizerNotFoundError(f"Tokenizer not found at {self._tokenizerPath}")
        tokenizer = BPETokenizer(self._tokenizerPath)
        vocabInfo = VocabInfo.from_json(self._vocabInfoPath.read_text())
        return tokenizer, vocabInfo
    
    def exists(self) -> bool:
        return self._tokenizerPath.exists() and self._vocabInfoPath.exists()
```

---

## 5. Pipelines

### `tokenizerTrainer.py`

```python
# apps/modules/tokenizer/pipelines/tokenizerTrainer.py
from tokenizers import Tokenizer, models, trainers, pre_tokenizers, decoders, processors
from tokenizers.normalizers import NFKC, Sequence
import hashlib, json

class TokenizerTrainer:
    def __init__(self, config: TokenizerConfig):
        self._config = config
        self._hfTokenizer = self._buildTokenizer()
    
    def _buildTokenizer(self) -> Tokenizer:
        tokenizer = Tokenizer(models.BPE(unk_token="<|unk|>"))
        tokenizer.normalizer = Sequence([NFKC()])
        tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=self._config.addPrefixSpace)
        tokenizer.decoder = decoders.ByteLevel()
        tokenizer.post_processor = processors.ByteLevel(trim_offsets=self._config.trimWhitespace)
        return tokenizer
    
    def train(self, corpusIterator: Iterator[str]) -> VocabInfo:
        trainer = trainers.BpeTrainer(
            vocab_size=self._config.vocabSize,
            min_frequency=self._config.minFrequency,
            special_tokens=self._config.specialTokens,
            show_progress=self._config.showProgress,
        )
        
        # Collect for length (progress bar)
        corpusList = list(corpusIterator)
        self._hfTokenizer.train_from_iterator(corpusList, trainer=trainer, length=len(corpusList))
        
        return self._computeVocabInfo()
    
    def _computeVocabInfo(self) -> VocabInfo:
        vocab = self._hfTokenizer.get_vocab()
        specialIds = {t: vocab[t] for t in self._config.specialTokens if t in vocab}
        
        # Validation sample pour stats
        sampleTexts = self._loadValidationSample(1000)
        totalChars = sum(len(t) for t in sampleTexts)
        totalTokens = sum(len(self._hfTokenizer.encode(t).ids) for t in sampleTexts)
        compressionRatio = totalChars / totalTokens if totalTokens > 0 else 0
        
        unkId = specialIds.get("<|unk|>", 3)
        oovCount = sum(1 for t in sampleTexts for id in self._hfTokenizer.encode(t).ids if id == unkId)
        oovRate = oovCount / totalTokens if totalTokens > 0 else 0
        
        configHash = hashlib.sha256(json.dumps(self._config.__dict__, sort_keys=True).encode()).hexdigest()[:16]
        
        return VocabInfo(
            vocabSize=len(vocab),
            specialTokenIds=specialIds,
            compressionRatio=compressionRatio,
            oovRate=oovRate,
            trainedAt=datetime.utcnow(),
            configHash=configHash
        )
    
    def _loadValidationSample(self, n: int) -> list[str]:
        # Charge échantillon depuis corpusRepo.loadClean() ou fichier dédié
        ...
    
    @property
    def hfTokenizer(self) -> Tokenizer:
        return self._hfTokenizer
```

### `corpusEncoder.py`

```python
# apps/modules/tokenizer/pipelines/corpusEncoder.py
import numpy as np
from apps.modules.corpus.models.corpusModel import CleanDocument

class CorpusEncoder:
    def __init__(
        self,
        tokenizer: BPETokenizer,
        outputDir: Path,
        shardSizeTokens: int = 100_000_000,
        dtype: str = "uint16",
        numWorkers: int = 4,
    ):
        self._tokenizer = tokenizer
        self._outputDir = outputDir
        self._shardSizeTokens = shardSizeTokens
        self._dtype = np.dtype(dtype)
        self._numWorkers = numWorkers
    
    def encodeCorpus(self, cleanDocsIterator: Iterator[CleanDocument]) -> EncodedCorpusStats:
        shardId = 0
        currentShardTokens = []
        currentShardOffsets = [0]
        docCount = 0
        totalTokens = 0
        langDist = {}
        
        for doc in cleanDocsIterator:
            ids = self._tokenizer.encode(doc.text, addSpecialTokens=True)
            tokenArray = np.array(ids, dtype=self._dtype)
            
            if len(currentShardTokens) + len(tokenArray) >= self._shardSizeTokens:
                self._flushShard(shardId, currentShardTokens, currentShardOffsets)
                shardId += 1
                currentShardTokens = []
                currentShardOffsets = [0]
            
            currentShardTokens.extend(tokenArray)
            currentShardOffsets.append(currentShardOffsets[-1] + len(tokenArray))
            
            docCount += 1
            totalTokens += len(tokenArray)
            langDist[doc.language] = langDist.get(doc.language, 0) + 1
        
        if currentShardTokens:
            self._flushShard(shardId, currentShardTokens, currentShardOffsets)
            shardId += 1
        
        return EncodedCorpusStats(
            totalTokens=totalTokens,
            totalDocuments=docCount,
            shardCount=shardId,
            avgTokensPerDoc=totalTokens / docCount if docCount > 0 else 0,
            languageDistribution=langDist
        )
    
    def _flushShard(self, shardId: int, tokens: list[int], offsets: list[int]) -> None:
        self._outputDir.mkdir(parents=True, exist_ok=True)
        binPath = self._outputDir / f"shard_{shardId:06d}.bin"
        idxPath = self._outputDir / f"shard_{shardId:06d}.idx"
        
        arr = np.array(tokens, dtype=self._dtype)
        np.save(binPath, arr)
        
        idxArr = np.array(offsets[:-1], dtype=np.uint64)
        np.save(idxPath, idxArr)
```

---

## 6. Service (`tokenizerService.py`)

```python
# apps/modules/tokenizer/services/tokenizerService.py
class TokenizerService:
    def __init__(
        self,
        trainer: TokenizerTrainer,
        encoder: CorpusEncoder,
        tokenizerRepo: TokenizerRepository,
        corpusRepo: CorpusRepository,
        jobRepo: JobRepository,
        workerPool: WorkerPool,
    ):
        ...
    
    def trainTokenizer(self, config: TokenizerConfig, corpusSampleSize: int = 10_000_000) -> Job:
        job = Job.create(type=JobType.TOKENIZER_TRAINING, config=config)
        self._jobRepo.save(job)
        self._workerPool.submit(self._runTokenizerTraining, job.id, corpusSampleSize)
        return job
    
    def _runTokenizerTraining(self, jobId: str, sampleSize: int):
        job = self._jobRepo.findById(jobId)
        try:
            sampleIter = self._corpusRepo.sampleClean(sampleSize)
            vocabInfo = self._trainer.train(sampleIter)
            self._tokenizerRepo.save(self._trainer.hfTokenizer, vocabInfo)
            job.status = JobStatus.COMPLETED
            job.result = vocabInfo
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
        finally:
            self._jobRepo.save(job)
    
    def encodeFullCorpus(self, tokenizerPath: Path) -> Job:
        job = Job.create(type=JobType.CORPUS_ENCODING)
        self._jobRepo.save(job)
        self._workerPool.submit(self._runCorpusEncoding, job.id, tokenizerPath)
        return job
    
    def _runCorpusEncoding(self, jobId: str, tokenizerPath: Path):
        job = self._jobRepo.findById(jobId)
        try:
            tokenizer = BPETokenizer(tokenizerPath)
            encoder = CorpusEncoder(tokenizer, self._corpusRepo.shardDir)
            docsIter = self._corpusRepo.loadClean()
            stats = encoder.encodeCorpus(docsIter)
            # Met à jour index via corpusRepo
            self._corpusRepo.saveShardInfo(encoder.getShardInfos())
            job.status = JobStatus.COMPLETED
            job.result = stats
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
        finally:
            self._jobRepo.save(job)
```

---

## 7. Controller (`tokenizerController.py`)

```python
# apps/modules/tokenizer/controllers/tokenizerController.py
tokenizerBlueprint = Blueprint("tokenizer", __name__, url_prefix="/api/tokenizer")

@tokenizerBlueprint.route("/train", methods=["POST"])
@requireAuth
@validateInput(TokenizerTrainRequest)
def trainTokenizer(validated: TokenizerTrainRequest, user: User):
    config = TokenizerConfig(**validated.model_dump())
    job = tokenizerService.trainTokenizer(config, validated.corpusSampleSize)
    return jsonify(JobResponse.fromJob(job)), 202

@tokenizerBlueprint.route("/encode", methods=["POST"])
@requireAuth
@validateInput(CorpusEncodeRequest)
def encodeCorpus(validated: CorpusEncodeRequest, user: User):
    job = tokenizerService.encodeFullCorpus(validated.tokenizerPath)
    return jsonify(JobResponse.fromJob(job)), 202

@tokenizerBlueprint.route("/status/<jobId>", methods=["GET"])
@requireAuth
def getTokenizerJobStatus(jobId: str, user: User):
    job = jobRepo.findById(jobId)
    if not job or job.userId != user.id:
        raise ResourceNotFoundError("Job")
    return jsonify(JobStatusResponse.fromJob(job))

@tokenizerBlueprint.route("/info", methods=["GET"])
@requireAuth
def getTokenizerInfo(user: User):
    if not tokenizerRepo.exists():
        return jsonify({"exists": False}), 404
    _, vocabInfo = tokenizerRepo.load()
    return jsonify({"exists": True, "vocabInfo": vocabInfo.__dict__})
```

---

## 8. Critères d'Acceptation

| Critère | Seuil |
|---------|-------|
| Vocabulaire | 32 000 tokens (± 5%) |
| Compression ratio | > 3.5 chars/token (FR/EN) |
| OOV rate | < 0.5% sur validation |
| Temps entraînement | < 30 min sur 10M docs (4 threads) |
| Temps encodage full corpus | < 2 heures (streaming, 4 workers) |
| Taille shards | ~100M tokens chacun |
| Reproductibilité | Même configHash → même tokenizer.json (byte-for-byte) |