# CODING RULES — Backend Python & Machine Learning

Ce document définit les règles, conventions et standards d'architecture pour le développement de la partie backend Python et du pipeline Machine Learning de **Riah Code**.

---

## 1. Conventions de Nommage & Style

### Règle d'or : CamelCase pour fonctions/variables, UPPER_SNAKE_CASE pour constantes

| Élément | Convention | Exemple |
|---------|------------|---------|
| Variables & Attributs | `camelCase` | `modelCheckpoint`, `batchSize`, `currentEpoch` |
| Fonctions & Méthodes | `camelCase` | `trainStep()`, `loadCheckpoint()`, `generateText()` |
| Paramètres | `camelCase` | `promptText: str`, `temperature: float = 0.8` |
| Constantes globales | `UPPER_SNAKE_CASE` | `DEFAULT_BLOCK_SIZE`, `MAX_GENERATION_LENGTH` |
| Classes & Exceptions | `PascalCase` | `ModelRunner`, `DatasetPipeline`, `ModelNotFoundError` |
| Modules & Fichiers | `camelCase` | `modelRunner.py`, `trainPipeline.py` |
| Packages / Dossiers | `camelCase` | `apps`, `services`, `repositories`, `decorators` |
| Variables privées / protégées | `_leadingUnderscore` | `self._model`, `self._cache` |
| Décorateurs (fonctions) | `camelCase` | `retryable`, `validateInput`, `requireAuth` |

### Exemples

```python
# CORRECT : camelCase pour variables, fonctions, méthodes
def trainStep(model: nn.Module, batch: torch.Tensor, optimizer: Optimizer) -> float:
    model.train()
    loss = model(batch)
    optimizer.zeroGrad()
    loss.backward()
    optimizer.step()
    return loss.item()

class ModelRunner:
    def __init__(self, modelConfig: ModelConfig):
        self._model = self._buildModel(modelConfig)
        self._currentEpoch = 0
    
    def runTraining(self, dataLoader: DataLoader, epochs: int) -> TrainingResult:
        for epoch in range(epochs):
            self._currentEpoch = epoch
            self._trainEpoch(dataLoader)
        return TrainingResult(losses=self._losses)

# CORRECT : UPPER_SNAKE_CASE pour constantes
MAX_GENERATION_LENGTH = 2048
DEFAULT_LEARNING_RATE = 3e-4
DEFAULT_BATCH_SIZE = 32

# INTERDIT : snake_case pour fonctions/variables
# def train_step(model, batch, optimizer):  # NON
#     total_loss = model(batch)              # NON
#     return total_loss                      # NON
```

---

## 2. Typage Strict & Type Hints

Toute signature de fonction, méthode ou constructeur doit comporter des annotations de types complètes (`typing` / built-in types Python 3.10+).

### Règles impératives
- Toujours annoter les paramètres et la valeur de retour (`-> ReturnType`).
- Utiliser `Optional[T]` (ou `T | None`) pour les valeurs pouvant être `None`.
- Préférer les structures typées (`dataclass` ou `Pydantic BaseModel`) aux dictionnaires anonymes `dict[str, Any]` pour les données métier et les configurations.
- Pas de `Any` non justifié.

```python
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import torch

@dataclass(frozen=True)
class GenerationOptions:
    maxTokens: int = 128
    temperature: float = 0.7
    topK: Optional[int] = 50
    repetitionPenalty: float = 1.1

def generateTokens(
    prompt: str,
    checkpointPath: Path,
    options: GenerationOptions
) -> str:
    """Génère du texte conditionné par le prompt et le checkpoint."""
    ...
```

---

## 3. Architecture Logicielle : Model-Service-Controller + Repository Pattern

Le backend sépare strictement :
- **Models** : Entités de domaine, dataclasses, schémas Pydantic
- **Repositories** : Accès aux données/fichiers (checkpoints, métriques, corpus)
- **Services** : Logique métier pure (orchestration, règles de gestion)
- **Controllers** : Couche HTTP (Flask Blueprints), sérialisation, validation requête
- **Decorators** : Fonctions transverses (auth, validation, retry, logging) dans `decorators/`

```
apps/
├── controllers/       # Couche HTTP : routes Flask, request/response handling
├── decorators/        # Décorateurs transverses (seules fonctions autorisées ici)
│   ├── auth.py
│   ├── validation.py
│   ├── retry.py
│   └── logging.py
├── models/            # Entités de domaine, schémas, DTOs
│   ├── checkpoint.py
│   ├── job.py
│   ├── dataset.py
│   └── training.py
├── repositories/      # Accès données (fichiers, JSONL, SQLite, cloud storage)
│   ├── checkpointRepository.py
│   ├── jobRepository.py
│   └── metricsRepository.py
├── services/          # Logique métier pure (orchestration, règles de gestion)
│   ├── trainingService.py
│   ├── inferenceService.py
│   ├── jobService.py
│   └── datasetService.py
├── ml/                # Briques ML découplées (Modèles, Tokenizers, Samplers)
│   ├── transformer.py
│   ├── tokenizer.py
│   └── sampler.py
├── pipelines/         # Pipelines de données (Data cleaner, Corpus builders)
│   ├── dataCleaner.py
│   └── corpusBuilder.py
├── config.py          # Configuration par environnement
└── __init__.py        # Application factory (createApp)
```

### Règles d'architecture

1. **Controllers** : Uniquement validation requête → délégation au Service → retour DTO JSON. Pas de logique métier.
2. **Services** : Logique métier pure, sans état, testables. Injection de dépendances (Repositories).
3. **Repositories** : Seule couche qui touche au stockage (fichiers, DB, S3). Abstraction complète.
4. **Models** : Entités immuables (`frozen=True` dataclasses) ou Pydantic. Représentent le domaine.
5. **Decorators** : Seules fonctions autorisées hors classes. Placées dans `apps/decorators/`.
6. **ML & Pipelines** : Classes pures, sans dépendance Flask/HTTP. Réutilisables par CLI et API.

### Exemple structure MVC + Repository

```python
# apps/models/checkpoint.py
@dataclass(frozen=True)
class Checkpoint:
    id: str
    name: str
    path: Path
    epoch: int
    step: int
    metrics: dict[str, float]
    createdAt: datetime

# apps/repositories/checkpointRepository.py
class CheckpointRepository:
    def __init__(self, baseDir: Path):
        self._baseDir = baseDir
    
    def findById(self, checkpointId: str) -> Optional[Checkpoint]:
        ...
    
    def save(self, checkpoint: Checkpoint) -> Checkpoint:
        ...
    
    def listAll(self) -> list[Checkpoint]:
        ...

# apps/services/trainingService.py
class TrainingService:
    def __init__(
        self,
        checkpointRepo: CheckpointRepository,
        modelRunner: ModelRunner
    ):
        self._checkpointRepo = checkpointRepo
        self._modelRunner = modelRunner
    
    def startTraining(self, config: TrainingConfig) -> Job:
        job = Job.create(config)
        self._jobRepo.save(job)
        # Lancement en background via worker
        return job
    
    def resumeFromCheckpoint(self, checkpointId: str, config: TrainingConfig) -> Job:
        checkpoint = self._checkpointRepo.findById(checkpointId)
        if not checkpoint:
            raise CheckpointNotFoundError(checkpointId)
        return self.startTraining(config.withCheckpoint(checkpoint))

# apps/controllers/trainingController.py
@trainingBlueprint.route("/jobs", methods=["POST"])
@validateInput(TrainingRequestSchema)
@requireAuth
def createTrainingJob(validatedData: TrainingRequest, user: User) -> Response:
    config = TrainingConfig.fromRequest(validatedData, user.id)
    job = trainingService.startTraining(config)
    return jsonify(JobResponse.fromJob(job)), 201
```

---

## 4. Décorateurs : Seules Fonctions Autorisées

Tous les décorateurs sont des **fonctions pures** dans `apps/decorators/`. Aucune logique métier dans les décorateurs.

```
apps/decorators/
├── __init__.py           # Exports publics
├── auth.py               # requireAuth, optionalAuth, requireRole
├── validation.py         # validateInput, validateQuery, validateParams
├── retry.py              # retryable, circuitBreaker
├── logging.py            # logExecution, logErrors
└── rateLimit.py          # rateLimited
```

### Exemples

```python
# apps/decorators/auth.py
def requireAuth(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        user = authService.validateToken(token)
        if not user:
            raise UnauthorizedError("Token invalide ou expiré")
        return func(user, *args, **kwargs)
    return wrapper

def requireRole(*roles: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(user: User, *args, **kwargs):
            if user.role not in roles:
                raise ForbiddenError("Rôle insuffisant")
            return func(user, *args, **kwargs)
        return wrapper
    return decorator

# apps/decorators/validation.py
def validateInput(schema: type[BaseModel]) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                validated = schema(**request.get_json())
            except ValidationError as e:
                raise InvalidInputError(e.errors())
            return func(validated, *args, **kwargs)
        return wrapper
    return decorator
```

---

## 5. Gestion des Concurrences & Jobs Longs (Background Tasks)

### Bonnes pratiques
- Isoler les exécutions longues dans des workers/threads supervisés avec état persistant.
- Fournir un mécanisme de signal d'annulation (`threading.Event` ou token d'annulation vérifié à chaque pas/époque).
- Consigner l'état (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`) et les métriques de façon atomique (JSONL ou SQLite).
- Empêcher les race conditions lors du chargement/sélection concurrente de checkpoints.

```python
# apps/services/jobService.py
class JobService:
    def __init__(self, jobRepo: JobRepository, workerPool: WorkerPool):
        self._jobRepo = jobRepo
        self._workerPool = workerPool
    
    def submitJob(self, job: Job) -> Job:
        job.status = JobStatus.PENDING
        self._jobRepo.save(job)
        self._workerPool.submit(self._executeJob, job.id)
        return job
    
    def _executeJob(self, jobId: str) -> None:
        job = self._jobRepo.findById(jobId)
        if not job:
            return
        
        cancelToken = CancellationToken()
        job.cancelToken = cancelToken
        job.status = JobStatus.RUNNING
        self._jobRepo.save(job)
        
        try:
            result = trainingService.run(job.config, cancelToken)
            job.status = JobStatus.COMPLETED
            job.result = result
        except CancellationException:
            job.status = JobStatus.CANCELLED
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
        finally:
            self._jobRepo.save(job)
```

---

## 6. Bonnes Pratiques Machine Learning & PyTorch

1. **Reproductibilité & Seeds** : Toujours permettre un seed explicite (`torch.manualSeed`, `numpy.random.seed`).
2. **Gestion des Périphériques (`device`)** : Détecter automatiquement `torch.device("cuda" if torch.cuda.isAvailable() else "cpu")`. Ne jamais forcer `cuda` en dur.
3. **Mode Évaluation & Grad** : Pour l'inférence : `model.eval()` + `with torch.inferenceMode():`.
4. **Sécurité & Chemins** : Valider que tout chemin client se trouve dans le répertoire autorisé (`Path.resolve().isRelativeTo(baseDir)`).
5. **Gestion Mémoire** : Libérer tensors volumineux + `torch.cuda.emptyCache()` à l'arrêt/rotation checkpoint.

```python
# apps/ml/modelRunner.py
class ModelRunner:
    def __init__(self, config: ModelConfig):
        self._config = config
        self._device = self._resolveDevice(config.devicePreference)
        self._model = self._buildModel().to(self._device)
    
    def _resolveDevice(self, preference: str) -> torch.device:
        if preference == "auto":
            return torch.device("cuda" if torch.cuda.isAvailable() else "cpu")
        return torch.device(preference)
    
    def generate(self, prompt: str, options: GenerationOptions) -> str:
        self._model.eval()
        with torch.inferenceMode():
            tokens = self._tokenizer.encode(prompt)
            generated = self._sample(tokens, options)
        return self._tokenizer.decode(generated)
```

---

## 7. Gestion des Erreurs & Réponses API

### Hiérarchie d'exceptions (toutes dans `apps/models/errors.py`)

```python
class RiahAppError(Exception):
    """Exception de base de l'application."""
    statusCode: int = 500
    errorCode: str = "INTERNAL_ERROR"
    
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class ResourceNotFoundError(RiahAppError):
    statusCode = 404
    errorCode = "RESOURCE_NOT_FOUND"

class InvalidJobStateError(RiahAppError):
    statusCode = 409
    errorCode = "INVALID_JOB_STATE"

class ValidationError(RiahAppError):
    statusCode = 400
    errorCode = "VALIDATION_ERROR"

class UnauthorizedError(RiahAppError):
    statusCode = 401
    errorCode = "UNAUTHORIZED"

class ForbiddenError(RiahAppError):
    statusCode = 403
    errorCode = "FORBIDDEN"

class CheckpointNotFoundError(ResourceNotFoundError):
    errorCode = "CHECKPOINT_NOT_FOUND"
```

### Format d'erreur JSON (standardisé)

```json
{
  "error": {
    "code": "CHECKPOINT_NOT_FOUND",
    "message": "Le checkpoint spécifié n'existe pas ou est corrompu.",
    "details": { "checkpointId": "ckpt-123" }
  }
}
```

### Règle : Pas de `except Exception: pass`
Toujours logger avec `logger.exception()` avant traitement.

---

## 8. Journalisation (Logging)

- Module standard `logging` configuré au niveau application.
- Pas de `print()` — utiliser `logger.debug()`, `logger.info()`, `logger.warning()`, `logger.error()`.
- Inclure identifiants pertinents (`runId`, `jobId`, `epoch`, `step`) dans les messages.
- Structured logging recommandé (JSON) pour agrégation.

```python
logger.info("Training started", extra={"jobId": job.id, "epoch": 0, "batchSize": 32})
logger.error("Checkpoint load failed", extra={"checkpointId": ckptId}, exc_info=True)
```

---

## 9. Tests & Validation

- Framework : `pytest`.
- Emplacement : dossier `tests/` miroir de `apps/`.
- **Tests unitaires** pour :
  - Models (sérialisation, validation)
  - Repositories (CRUD, edge cases)
  - Services (logique métier, règles de gestion)
  - ML (sampling, tokenization, forward pass)
  - Decorators (comportement isolé)
- **Tests d'intégration** pour :
  - Cycle de vie d'un job (lancement, arrêt, statut)
  - Routes API Flask (contrats `PRD RC_5`)
  - Pipeline données complet

```python
# tests/services/testTrainingService.py
def testStartTrainingCreatesJobAndSubmitsToWorker(trainingService, mockWorkerPool):
    config = TrainingConfig(modelName="test", epochs=3)
    job = trainingService.startTraining(config)
    
    assert job.status == JobStatus.PENDING
    mockWorkerPool.submit.assert_called_once()
```

---

## 10. Respect des Spécifications PRD

Toute implémentation doit s'aligner sur les contrats définis dans `PRD/` :

- `RC_1` : Cadrage & analyse existant
- `RC_2` : Pipeline de données
- `RC_3` : Tokenizer & corpus
- `RC_4` : Modèle & entraînement
- `RC_5` : API, Dashboard & Inférence (contrats routes, formats JSON)
- `RC_6` : Architecture cible & migration
- `RC_7` : Tests, qualité & acceptation

**Avant tout développement** : vérifier l'alignement avec le PRD concerné.

---

## 11. Anti-patterns Formellement Interdits

```python
# INTERDIT : snake_case
def train_model(model, data_loader): ...

# INTERDIT : logique métier dans controller
@bp.route("/train")
def train():
    model = loadModel()  # NON - ça va dans Service
    for epoch in range(10):
        trainEpoch(model)  # NON

# INTERDIT : repository accédant directement au FS dans un service
class TrainingService:
    def save(self, ckpt):
        with open("path", "w") as f:  # NON - passe par Repository
            json.dump(ckpt, f)

# INTERDIT : décorateur avec logique métier
def requireValidCheckpoint(func):
    def wrapper(ckptId):
        ckpt = Checkpoint.load(ckptId)  # NON - ça va dans Service/Repository
        return func(ckpt)
    return wrapper

# INTERDIT : état global mutable
_currentModel = None  # NON - injection de dépendances

# INTERDIT : except Exception: pass
try:
    risky()
except Exception:
    pass  # NON - toujours logger et traiter
```

---

## Résumé Rapide

| Catégorie | Convention |
|-----------|------------|
| Variables, fonctions, méthodes, params | `camelCase` |
| Constantes | `UPPER_SNAKE_CASE` |
| Classes, exceptions, DTOs | `PascalCase` |
| Fichiers, modules, packages | `camelCase` |
| Décorateurs (dans `decorators/`) | Fonctions `camelCase` |
| Architecture | Model → Repository → Service → Controller |
| ML/Pipelines | Classes pures, réutilisables CLI+API |
| Typage | Strict, dataclass/Pydantic, pas de `Any` |
| Erreurs | Hiérarchie `RiahAppError`, format JSON standard |
| Tests | `pytest`, miroirs `apps/`, unit + intégration |