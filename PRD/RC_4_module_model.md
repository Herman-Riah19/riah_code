# RC_4 — Module Model : Transformer, Entraînement & Inférence

## 1. Objectifs

Module **`model`** : Implémenter le Transformer Decoder-only, l'entraînement distribué, la gestion des checkpoints, et l'inférence (génération de texte).

**Sous-domaines** :
- **Architecture ML** : `transformer.py`, `attention.py`, `feedForward.py`, `embedding.py`, `normalization.py`, `loss.py`, `sampler.py`, `modelRunner.py`
- **Entraînement** : `TrainingService`, `TrainingLoop`, `ShardedDataset`
- **Inférence** : `InferenceService`, `ModelRunner` (chargement lazy, KV-cache, streaming)
- **Checkpoints** : `CheckpointRepository` (save/load/resume complet)

---

## 2. Structure Module `model`

```
apps/modules/model/
├── __init__.py
├── models/
│   ├── __init__.py
│   └── modelModel.py            # ModelConfig, ModelPresets, TrainingConfig, Checkpoint
├── repositories/
│   ├── __init__.py
│   ├── modelRepository.py       # Configs, presets
│   └── checkpointRepository.py  # Checkpoints entraînement
├── services/
│   ├── __init__.py
│   ├── trainingService.py       # startTraining, resumeTraining
│   └── inferenceService.py      # loadModel, generate, streamGenerate
├── ml/                          # Composants ML purs (réutilisables CLI + API)
│   ├── __init__.py
│   ├── transformer.py           # TransformerLM, TransformerBlock
│   ├── attention.py             # MultiHeadAttention (Flash/SDPA)
│   ├── feedForward.py           # SwiGLU, GELU
│   ├── embedding.py             # TokenEmbedding, RoPE
│   ├── normalization.py         # RMSNorm, LayerNorm
│   ├── loss.py                  # CrossEntropy + label smoothing
│   ├── sampler.py               # Temperature, top-k, top-p, penalty
│   └── modelRunner.py           # High-level: forward, generate, save/load
├── pipelines/
│   ├── __init__.py
│   ├── trainingLoop.py          # TrainingLoop (mixed precision, accum, checkpoint)
│   └── shardedDataset.py        # ShardedTokenDataset (IterableDataset)
└── controllers/
    ├── __init__.py
    ├── trainingController.py    # Blueprint /api/training
    └── inferenceController.py   # Blueprint /api/inference
```

---

## 3. Modèles de Domaine (`modelModel.py`)

```python
# apps/modules/model/models/modelModel.py
from dataclasses import dataclass, field
from typing import Literal
from pathlib import Path
from datetime import datetime

@dataclass(frozen=True)
class ModelConfig:
    # Architecture
    vocabSize: int = 32_000
    maxSeqLen: int = 2048
    nLayers: int = 12
    nHeads: int = 12
    nKvHeads: int | None = None        # GQA
    dim: int = 768
    dimFF: int | None = None
    
    # Normalization
    normType: Literal["rmsnorm", "layernorm"] = "rmsnorm"
    normEps: float = 1e-5
    
    # Attention
    attnImpl: Literal["eager", "flash", "sdpa"] = "sdpa"
    attnDropout: float = 0.0
    residDropout: float = 0.0
    useBias: bool = False
    useRoPE: bool = True
    ropeTheta: float = 10_000.0
    ropeScaling: dict | None = None
    
    # FFN
    activation: Literal["gelu", "swiglu", "geglu"] = "swiglu"
    ffnDropout: float = 0.0
    
    # Embedding
    tieEmbeddings: bool = True
    initStd: float = 0.02
    
    # Precision
    dtype: Literal["fp32", "fp16", "bf16"] = "bf16"
    
    # Compilation
    compileMode: Literal["default", "reduce-overhead", "max-autotune"] | None = "default"
    
    @property
    def nParams(self) -> int:
        embParams = self.vocabSize * self.dim
        attnParamsPerLayer = 4 * self.dim * self.dim
        ffnParamsPerLayer = 2 * self.dim * (self.dimFF or 4 * self.dim)
        layerParams = self.nLayers * (attnParamsPerLayer + ffnParamsPerLayer + 2 * self.dim)
        outParams = 0 if self.tieEmbeddings else self.vocabSize * self.dim
        return embParams + layerParams + outParams

MODEL_PRESETS = {
    "125M": ModelConfig(nLayers=12, nHeads=12, dim=768),
    "350M": ModelConfig(nLayers=24, nHeads=16, dim=1024),
    "760M": ModelConfig(nLayers=24, nHeads=16, dim=1536),
    "1.3B": ModelConfig(nLayers=24, nHeads=32, dim=2048),
}

@dataclass(frozen=True)
class TrainingConfig:
    modelConfig: ModelConfig
    trainShards: list[Path]
    valShards: list[Path]
    batchSize: int = 32
    microBatchSize: int | None = None
    seqLen: int = 2048
    numWorkers: int = 4
    
    optimizer: Literal["adamw", "adamw8bit", "lion"] = "adamw"
    lr: float = 3e-4
    minLr: float = 3e-5
    weightDecay: float = 0.1
    beta1: float = 0.9
    beta2: float = 0.95
    eps: float = 1e-8
    gradClip: float = 1.0
    
    scheduler: Literal["cosine", "cosine_warmup", "constant", "wsd"] = "cosine_warmup"
    warmupSteps: int = 2000
    decaySteps: int = 100_000
    
    maxSteps: int = 100_000
    maxEpochs: int | None = None
    gradientAccumulationSteps: int = 1
    evalInterval: int = 1000
    evalSteps: int = 100
    logInterval: int = 10
    
    checkpointDir: Path = Path("checkpoints")
    checkpointInterval: int = 5000
    keepLastNCheckpoints: int = 3
    saveOptimizer: bool = True
    saveRng: bool = True
    
    dtype: Literal["fp32", "fp16", "bf16"] = "bf16"
    useGradScaler: bool = True
    compileModel: bool = True
    tensorboard: bool = True
    
    seed: int = 42
    
    @property
    def effectiveBatchSize(self) -> int:
        return self.batchSize * self.gradientAccumulationSteps

@dataclass(frozen=True)
class Checkpoint:
    id: str
    path: Path
    step: int
    epoch: int
    loss: float
    valLoss: float | None
    modelConfig: ModelConfig
    trainingConfig: TrainingConfig | None
    createdAt: datetime
    isBest: bool = False
    metadata: dict = field(default_factory=dict)

@dataclass(frozen=True)
class GenerationOptions:
    maxTokens: int = 128
    temperature: float = 0.7
    topK: int | None = 50
    topP: float = 0.9
    repetitionPenalty: float = 1.1
    stopSequences: list[str] = field(default_factory=list)
    seed: int | None = None
```

---

## 4. Repository Checkpoints (`checkpointRepository.py`)

```python
# apps/modules/model/repositories/checkpointRepository.py
class CheckpointRepository:
    def __init__(self, baseDir: Path):
        self._baseDir = baseDir
        self._indexDb = baseDir / "checkpoints_index.sqlite"
        self._initDb()
    
    def save(self, checkpoint: Checkpoint) -> Checkpoint:
        # Sauvegarde .pt + métadonnées SQLite
        ...
    
    def findById(self, checkpointId: str) -> Checkpoint | None:
        ...
    
    def findLatest(self, modelName: str | None = None) -> Checkpoint | None:
        ...
    
    def findBest(self, modelName: str | None = None) -> Checkpoint | None:
        ...
    
    def listAll(self, limit: int = 50, offset: int = 0) -> list[Checkpoint]:
        ...
    
    def pruneOld(self, keepLastN: int = 3) -> int:
        # Supprime les plus anciens au-delà de keepLastN
        ...
```

---

## 5. Composants ML (dans `ml/`)

### `modelRunner.py` — High-level Interface

```python
# apps/modules/model/ml/modelRunner.py
class ModelRunner:
    def __init__(self, config: ModelConfig, device: torch.device | None = None):
        self._config = config
        self._device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model = TransformerLM(config).to(self._device)
        self._dtype = {"fp32": torch.float32, "fp16": torch.float16, "bf16": torch.bfloat16}[config.dtype]
        
        if config.compileModel and hasattr(torch, "compile"):
            self._model = torch.compile(self._model, mode=config.compileMode)
    
    @property
    def model(self) -> TransformerLM:
        return self._model
    
    def forward(self, inputIds: torch.Tensor) -> torch.Tensor:
        self._model.eval()
        with torch.inference_mode(), torch.amp.autocast("cuda", dtype=self._dtype):
            logits, _ = self._model(inputIds.to(self._device))
        return logits
    
    def generate(self, inputIds: torch.Tensor, options: GenerationOptions) -> torch.Tensor:
        sampler = Sampler(
            temperature=options.temperature,
            topK=options.topK,
            topP=options.topP,
            repetitionPenalty=options.repetitionPenalty,
            stopTokenIds=[self._config.eosTokenId] + [self._tokenizer.tokenToId(s) for s in options.stopSequences],
        )
        self._model.eval()
        with torch.inference_mode(), torch.amp.autocast("cuda", dtype=self._dtype):
            return self._model.generate(inputIds.to(self._device), options.maxTokens, sampler)
    
    def streamGenerate(self, inputIds: torch.Tensor, options: GenerationOptions) -> Iterator[int]:
        """Génère token par token pour streaming WebSocket."""
        sampler = Sampler(...)
        self._model.eval()
        with torch.inference_mode(), torch.amp.autocast("cuda", dtype=self._dtype):
            for tokenId in self._model.stream_generate(inputIds.to(self._device), options.maxTokens, sampler):
                yield tokenId
                if tokenId == sampler.eosTokenId:
                    break
    
    def loadCheckpoint(self, checkpoint: Checkpoint) -> None:
        state = torch.load(checkpoint.path, map_location="cpu", weights_only=True)
        self._model.load_state_dict(state["model"])
        # Optionnel: load optimizer, scheduler, RNG pour reprise
    
    def saveCheckpoint(self, path: Path, optimizer: torch.optim.Optimizer | None = None, 
                       scheduler=None, step: int = 0, epoch: int = 0, rng: dict | None = None) -> None:
        state = {
            "model": self._model.state_dict(),
            "optimizer": optimizer.state_dict() if optimizer else None,
            "scheduler": scheduler.state_dict() if scheduler else None,
            "step": step,
            "epoch": epoch,
            "rng": rng,
        }
        torch.save(state, path)
```

### `sampler.py` — Stratégies d'échantillonnage

```python
# apps/modules/model/ml/sampler.py
class Sampler:
    def __init__(
        self,
        temperature: float = 1.0,
        topK: int | None = None,
        topP: float = 1.0,
        repetitionPenalty: float = 1.0,
        stopTokenIds: list[int] = None,
        eosTokenId: int = 0,
    ):
        self.temperature = temperature
        self.topK = topK
        self.topP = topP
        self.repetitionPenalty = repetitionPenalty
        self.stopTokenIds = set(stopTokenIds or [])
        self.eosTokenId = eosTokenId
    
    def sample(self, logits: torch.Tensor, generatedTokens: list[int] = None) -> torch.Tensor:
        # logits: (batch, vocab)
        if self.temperature != 1.0:
            logits = logits / self.temperature
        
        # Repetition penalty
        if self.repetitionPenalty != 1.0 and generatedTokens:
            for tokenId in set(generatedTokens):
                logits[:, tokenId] /= self.repetitionPenalty
        
        # Top-k
        if self.topK is not None:
            topK = min(self.topK, logits.size(-1))
            indices_to_remove = logits < torch.topk(logits, topK)[0][..., -1:]
            logits = logits.masked_fill(indices_to_remove, float("-inf"))
        
        # Top-p (nucleus)
        if self.topP < 1.0:
            sorted_logits, sorted_indices = torch.sort(logits, descending=True)
            cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
            sorted_indices_to_remove = cumulative_probs > self.topP
            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
            sorted_indices_to_remove[..., 0] = 0
            indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
            logits = logits.masked_fill(indices_to_remove, float("-inf"))
        
        probs = F.softmax(logits, dim=-1)
        next_token = torch.multinomial(probs, num_samples=1)
        return next_token
    
    def stream_generate(self, inputIds: torch.Tensor, maxTokens: int) -> Iterator[int]:
        generated = inputIds[0].tolist()
        for _ in range(maxTokens):
            logits, _ = self._model(inputIds[:, -self._config.maxSeqLen:])
            next_token = self.sample(logits[:, -1, :], generated)
            token_id = next_token.item()
            yield token_id
            generated.append(token_id)
            if token_id in self.stopTokenIds:
                break
            inputIds = torch.cat([inputIds, next_token.unsqueeze(0)], dim=1)
```

---

## 6. Pipeline Entraînement (`trainingLoop.py`)

```python
# apps/modules/model/pipelines/trainingLoop.py
class TrainingLoop:
    def __init__(self, config: TrainingConfig, modelRunner: ModelRunner, tokenizer: BPETokenizer):
        self.config = config
        self.modelRunner = modelRunner
        self.tokenizer = tokenizer
        self.device = modelRunner._device
        self.dtype = modelRunner._dtype
        self.model = modelRunner.model
        
        # Optimizer, scheduler, scaler
        self.optimizer = self._createOptimizer()
        self.scheduler = self._createScheduler()
        self.scaler = torch.amp.GradScaler("cuda", enabled=config.useGradScaler and config.dtype == "fp16")
        
        # Data
        self.trainLoader = self._createLoader(config.trainShards, shuffle=True)
        self.valLoader = self._createLoader(config.valShards, shuffle=False)
        
        # State
        self.step = 0
        self.epoch = 0
        self.bestValLoss = float("inf")
        self.cancelToken = CancellationToken()
        
        # Logging
        self.logFile = config.checkpointDir / "training_log.jsonl"
        self.tbWriter = SummaryWriter(config.checkpointDir / "tensorboard") if config.tensorboard else None
    
    def train(self) -> TrainingResult:
        self.model.train()
        accumSteps = self.config.gradientAccumulationSteps
        
        ctx = torch.amp.autocast("cuda", dtype=self.dtype) if self.dtype != torch.float32 else nullcontext()
        dataIter = iter(self.trainLoader)
        
        while self.step < self.config.maxSteps and not self.cancelToken.isCancelled:
            self.optimizer.zero_grad(set_to_none=True)
            
            for microStep in range(accumSteps):
                try:
                    batch = next(dataIter)
                except StopIteration:
                    self.epoch += 1
                    dataIter = iter(self.trainLoader)
                    batch = next(dataIter)
                
                inputIds = batch["input_ids"].to(self.device, non_blocking=True)
                targets = batch["labels"].to(self.device, non_blocking=True)
                
                with ctx:
                    logits, loss = self.model(inputIds, targets)
                    loss = loss / accumSteps
                
                self.scaler.scale(loss).backward()
            
            if self.config.gradClip > 0:
                self.scaler.unscale_(self.optimizer)
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.gradClip)
            
            self.scaler.step(self.optimizer)
            self.scaler.update()
            self.scheduler.step()
            self.step += 1
            
            if self.step % self.config.logInterval == 0:
                self._logMetrics(loss.item() * accumSteps)
            
            if self.step % self.config.evalInterval == 0:
                valLoss = self.evaluate()
                self._logMetrics(valLoss, prefix="val")
                if valLoss < self.bestValLoss:
                    self.bestValLoss = valLoss
                    self.saveCheckpoint("best")
            
            if self.step % self.config.checkpointInterval == 0:
                self.saveCheckpoint(f"step_{self.step}")
        
        self.saveCheckpoint("final")
        return TrainingResult(self.step, self.bestValLoss, self.step * self.config.effectiveBatchSize * self.config.seqLen)
    
    @torch.inference_mode()
    def evaluate(self) -> float:
        self.model.eval()
        losses = []
        for i, batch in enumerate(self.valLoader):
            if i >= self.config.evalSteps: break
            inputIds = batch["input_ids"].to(self.device)
            targets = batch["labels"].to(self.device)
            with torch.amp.autocast("cuda", dtype=self.dtype):
                _, loss = self.model(inputIds, targets)
            losses.append(loss.item())
        self.model.train()
        return sum(losses) / len(losses)
    
    def saveCheckpoint(self, tag: str) -> Path:
        ckptPath = self.config.checkpointDir / f"checkpoint_{tag}.pt"
        rng = {
            "python": random.getstate(),
            "numpy": np.random.get_state(),
            "torch": torch.get_rng_state(),
            "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
        } if self.config.saveRng else None
        self.modelRunner.saveCheckpoint(ckptPath, self.optimizer, self.scheduler, self.step, self.epoch, rng)
        self._pruneCheckpoints()
        return ckptPath
    
    def loadCheckpoint(self, ckptPath: Path) -> None:
        state = torch.load(ckptPath, map_location="cpu")
        self.model.load_state_dict(state["model"])
        if state["optimizer"]: self.optimizer.load_state_dict(state["optimizer"])
        self.scheduler.load_state_dict(state["scheduler"])
        self.step = state["step"]
        self.epoch = state["epoch"]
        self.bestValLoss = state.get("best_val_loss", float("inf"))
        if state["rng"] and self.config.saveRng:
            random.setstate(state["rng"]["python"])
            np.random.set_state(state["rng"]["numpy"])
            torch.set_rng_state(state["rng"]["torch"])
            if state["rng"]["cuda"]:
                torch.cuda.set_rng_state_all(state["rng"]["cuda"])
    
    def cancel(self):
        self.cancelToken.cancel()
```

---

## 7. Services

### `trainingService.py`

```python
# apps/modules/model/services/trainingService.py
class TrainingService:
    def __init__(
        self,
        modelFactory: Callable[[ModelConfig], ModelRunner],
        tokenizerRepo: TokenizerRepository,
        checkpointRepo: CheckpointRepository,
        corpusRepo: CorpusRepository,
        jobRepo: JobRepository,
        workerPool: WorkerPool,
    ):
        ...
    
    def startTraining(self, config: TrainingConfig, userId: str) -> Job:
        job = Job.create(type=JobType.TRAINING, config=config, userId=userId)
        self._jobRepo.save(job)
        self._workerPool.submit(self._runTraining, job.id)
        return job
    
    def resumeTraining(self, checkpointId: str, config: TrainingConfig, userId: str) -> Job:
        checkpoint = self._checkpointRepo.findById(checkpointId)
        if not checkpoint: raise CheckpointNotFoundError(checkpointId)
        job = Job.create(type=JobType.TRAINING, config=config, userId=userId, resumeFrom=checkpointId)
        self._jobRepo.save(job)
        self._workerPool.submit(self._runTraining, job.id)
        return job
    
    def _runTraining(self, jobId: str):
        job = self._jobRepo.findById(jobId)
        tokenizer, _ = self._tokenizerRepo.load()
        modelRunner = self._modelFactory(job.config.modelConfig)
        loop = TrainingLoop(job.config, modelRunner, tokenizer)
        
        if job.resumeFrom:
            ckpt = self._checkpointRepo.findById(job.resumeFrom)
            loop.loadCheckpoint(ckpt.path)
        
        try:
            result = loop.train()
            job.status = JobStatus.COMPLETED
            job.result = result
        except CancellationException:
            job.status = JobStatus.CANCELLED
            loop.saveCheckpoint("cancelled")
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
        finally:
            self._jobRepo.save(job)
```

### `inferenceService.py`

```python
# apps/modules/model/services/inferenceService.py
class InferenceService:
    def __init__(
        self,
        tokenizerRepo: TokenizerRepository,
        checkpointRepo: CheckpointRepository,
        modelFactory: Callable[[ModelConfig], ModelRunner],
        modelCache: LRUCache[str, ModelRunner],  # Cache LRU modèles chargés
    ):
        ...
    
    def loadModel(self, checkpointId: str | None = None) -> ModelRunner:
        if checkpointId and checkpointId in self._modelCache:
            return self._modelCache[checkpointId]
        
        if checkpointId:
            checkpoint = self._checkpointRepo.findById(checkpointId)
        else:
            checkpoint = self._checkpointRepo.findBest()
        
        if not checkpoint:
            raise NoModelAvailableError("Aucun checkpoint disponible")
        
        modelRunner = self._modelFactory(checkpoint.modelConfig)
        modelRunner.loadCheckpoint(checkpoint)
        
        self._modelCache.put(checkpoint.id, modelRunner)
        return modelRunner
    
    def generate(self, prompt: str, options: GenerationOptions, checkpointId: str | None = None) -> str:
        tokenizer, _ = self._tokenizerRepo.load()
        modelRunner = self.loadModel(checkpointId)
        inputIds = torch.tensor([tokenizer.encode(prompt)], dtype=torch.long)
        outputIds = modelRunner.generate(inputIds, options)
        return tokenizer.decode(outputIds[0].tolist())
    
    def streamGenerate(self, prompt: str, options: GenerationOptions, checkpointId: str | None = None) -> Iterator[str]:
        tokenizer, _ = self._tokenizerRepo.load()
        modelRunner = self.loadModel(checkpointId)
        inputIds = torch.tensor([tokenizer.encode(prompt)], dtype=torch.long)
        for tokenId in modelRunner.streamGenerate(inputIds, options):
            yield tokenizer.decode([tokenId])
```

---

## 8. Controllers

### `trainingController.py`
```python
trainingBlueprint = Blueprint("training", __name__, url_prefix="/api/training")

@trainingBlueprint.route("/jobs", methods=["POST"])
@requireAuth @validateInput(TrainingStartRequest)
def startTraining(validated: TrainingStartRequest, user: User):
    config = TrainingConfig(...)
    job = trainingService.startTraining(config, user.id)
    return jsonify(JobResponse.fromJob(job)), 202

@trainingBlueprint.route("/jobs/<jobId>/resume", methods=["POST"])
@requireAuth
def resumeTraining(jobId: str, user: User):
    job = jobRepo.findById(jobId)
    config = TrainingConfig.fromJob(job)
    job = trainingService.resumeTraining(job.resumeFrom, config, user.id)
    return jsonify(JobResponse.fromJob(job))

@trainingBlueprint.route("/jobs/<jobId>/cancel", methods=["POST"])
@requireAuth
def cancelTraining(jobId: str, user: User):
    job = jobRepo.findById(jobId)
    workerPool.cancel(jobId)
    return jsonify({"status": "cancelling"})

@trainingBlueprint.route("/jobs/<jobId>", methods=["GET"])
@requireAuth
def getTrainingJob(jobId: str, user: User):
    job = jobRepo.findById(jobId)
    return jsonify(JobDetailResponse.fromJob(job))

@trainingBlueprint.route("/checkpoints", methods=["GET"])
@requireAuth
def listCheckpoints(user: User):
    checkpoints = checkpointRepo.listAll()
    return jsonify([CheckpointResponse.fromCheckpoint(c) for c in checkpoints])
```

### `inferenceController.py`
```python
inferenceBlueprint = Blueprint("inference", __name__, url_prefix="/api/inference")

@inferenceBlueprint.route("/generate", methods=["POST"])
@requireAuth @validateInput(GenerateRequest)
def generate(validated: GenerateRequest, user: User):
    text = inferenceService.generate(validated.prompt, validated.options, validated.checkpointId)
    return jsonify(GenerateResponse(text=text))

@inferenceBlueprint.route("/models", methods=["GET"])
@requireAuth
def listModels(user: User):
    checkpoints = checkpointRepo.listAll()
    return jsonify([ModelInfo.fromCheckpoint(c) for c in checkpoints])
```

---

## 9. Critères d'Acceptation

| Critère | Seuil |
|---------|-------|
| Convergence | Loss val < 3.0 (ppl < 20) après 100k steps (125M) |
| Throughput | > 50k tokens/sec/GPU (A100 40GB, bf16, compile) |
| Reprise checkpoint | Identique bit-à-bit (loss, step, RNG) |
| Mémoire VRAM | < 14GB (125M, bs=32, seq=2048, bf16) |
| Stabilité | Pas de NaN/Inf sur 100k steps |
| Checkpoint taille | < 2GB (modèle + optimizer + RNG) |
| Latence inférence | < 100ms/token streaming, < 2s first token |
| Cache modèles | LRU éviction, chargement lazy |