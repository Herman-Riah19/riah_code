# RC_7 — Tests, Qualité & Critères d'Acceptation

## 1. Stratégie de Test Globale

### Pyramide de Test

```
                    ┌─────────────────┐
                    │   E2E Tests     │  ← Peu, critiques (Cypress/Playwright)
                    │  (User flows)   │
               ┌────┴────────────────┴────┐
               │   Integration Tests      │  ← API, DB, ML pipelines
               │  (Service + Repository)  │
         ┌─────┴──────────────────────────┴─────┐
         │         Unit Tests                   │  ← Beaucoup, rapides, isolés
         │  (Models, Services, ML, Pipelines)   │
         └──────────────────────────────────────┘
```

### Répartition Cible

| Niveau | % Couverture | Outils | Vitesse |
|--------|--------------|--------|---------|
| Unit | 85%+ | pytest, hypothesis | < 30s total |
| Integration | 70%+ | pytest, testcontainers | < 2min |
| E2E | 10 chemins critiques | Playwright | < 5min |

---

## 2. Structure Tests

```
tests/
├── conftest.py                  # Fixtures globales, config pytest
├── pytest.ini                   # Config pytest
├── unit/
│   ├── test_models/             # Entités domaine (dataclasses, validation)
│   │   ├── test_corpusModel.py
│   │   ├── test_tokenizerModel.py
│   │   ├── test_modelModel.py
│   │   └── test_chatModel.py
│   ├── test_services/           # Logique métier pure (mock repositories)
│   │   ├── test_corpusService.py
│   │   ├── test_tokenizerService.py
│   │   ├── test_trainingService.py
│   │   ├── test_inferenceService.py
│   │   └── test_chatService.py
│   ├── test_repositories/       # Repository logic (DB en mémoire)
│   │   ├── test_corpusRepository.py
│   │   ├── test_tokenizerRepository.py
│   │   ├── test_checkpointRepository.py
│   │   └── test_chatRepository.py
│   ├── test_ml/                 # Composants ML purs
│   │   ├── test_transformer.py
│   │   ├── test_attention.py
│   │   ├── test_sampler.py
│   │   └── test_modelRunner.py
│   ├── test_pipelines/          # Pipelines données
│   │   ├── test_htmlCleaner.py
│   │   ├── test_textNormalizer.py
│   │   ├── test_qualityFilter.py
│   │   ├── test_deduplicator.py
│   │   └── test_shardWriter.py
│   └── test_decorators/         # Décorateurs transverses
│       ├── test_auth.py
│       ├── test_validation.py
│       └── test_retry.py
├── integration/
│   ├── test_api/                # API complètes (TestClient Flask)
│   │   ├── test_corpusController.py
│   │   ├── test_tokenizerController.py
│   │   ├── test_trainingController.py
│   │   ├── test_inferenceController.py
│   │   └── test_chatController.py
│   ├── test_training_loop/      # Boucle entraînement complète (mock data)
│   ├── test_inference_flow/     # Chargement modèle → génération
│   └── test_chat_flow/          # Session → message → réponse
├── e2e/
│   ├── test_chat_ui.spec.ts     # Playwright: chat complet
│   ├── test_training_dashboard.spec.ts
│   └── test_data_pipeline.spec.ts
├── fixtures/
│   ├── sample_documents.jsonl
│   ├── sample_checkpoints/
│   └── sample_conversations.json
└── utils/
    ├── mock_factories.py        # Factories pour tests
    ├── torch_test_utils.py      # Helpers PyTorch
    └── flask_test_utils.py      # Helpers Flask
```

---

## 3. Configuration Pytest

```ini
# tests/pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --strict-config
    --tb=short
    -ra
    --cov=apps
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (requires DB, services)
    e2e: End-to-end tests (requires full stack)
    slow: Tests taking > 10s
    gpu: Tests requiring GPU
    ml: ML-specific tests
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

```python
# tests/conftest.py
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

# Fixtures globales
@pytest.fixture(scope="session")
def tempDataDir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def mockCorpusRepo():
    repo = MagicMock(spec=CorpusRepository)
    repo.saveRaw.return_value = 1
    repo.loadRaw.return_value = iter([])
    repo.saveClean.return_value = 1
    repo.loadClean.return_value = iter([])
    return repo

@pytest.fixture
def mockTokenizerRepo():
    repo = MagicMock(spec=TokenizerRepository)
    repo.exists.return_value = True
    tokenizer = MagicMock(spec=BPETokenizer)
    tokenizer.vocabSize = 32000
    tokenizer.eosTokenId = 0
    tokenizer.padTokenId = 1
    tokenizer.unkTokenId = 2
    tokenizer.encode.return_value = [1, 2, 3, 0]
    tokenizer.decode.return_value = "test"
    repo.load.return_value = (tokenizer, MagicMock(vocabSize=32000))
    return repo

@pytest.fixture
def mockCheckpointRepo():
    repo = MagicMock(spec=CheckpointRepository)
    repo.findById.return_value = None
    repo.findBest.return_value = None
    repo.listAll.return_value = []
    return repo

@pytest.fixture
def mockJobRepo():
    repo = MagicMock(spec=JobRepository)
    repo.save.return_value = None
    repo.findById.return_value = None
    return repo

@pytest.fixture
def mockWorkerPool():
    pool = MagicMock(spec=WorkerPool)
    pool.submit.return_value = None
    return pool

# Fixtures ML
@pytest.fixture
def tinyModelConfig():
    return ModelConfig(
        vocabSize=1000,
        maxSeqLen=64,
        nLayers=2,
        nHeads=4,
        dim=128,
        dtype="fp32",
        compileModel=False
    )

@pytest.fixture
def tinyModel(tinyModelConfig):
    return TransformerLM(tinyModelConfig)

# Fixtures données
@pytest.fixture
def sampleRawDocuments():
    return [
        RawDocument.create("wikipedia", "https://wiki.test/1", "fr", "Bonjour le monde.", {}),
        RawDocument.create("bible_gateway", "https://bible.test/1", "fr", "Au commencement...", {"book": "Genèse", "chapter": 1}),
    ]

@pytest.fixture
def sampleCleanDocuments():
    return [
        CleanDocument(id="1", source="wikipedia", language="fr", text="Bonjour le monde.", qualityScore=0.9, tokenCount=5, cleanedAt=datetime.utcnow()),
    ]
```

---

## 4. Exemples Tests Unitaires

### Models (Validation, Sérialisation)

```python
# tests/unit/test_models/test_tokenizerModel.py
import pytest
from apps.modules.tokenizer.models.tokenizerModel import TokenizerConfig, VocabInfo, BPETokenizer

class TestTokenizerConfig:
    def test_default_values(self):
        config = TokenizerConfig()
        assert config.vocabSize == 32_000
        assert config.minFrequency == 2
        assert "<|endoftext|>" in config.specialTokens
        assert config.byteFallback is True
    
    def test_custom_values(self):
        config = TokenizerConfig(vocabSize=16_000, specialTokens=["<|pad|>", "<|eos|>"])
        assert config.vocabSize == 16_000
        assert config.specialTokens == ["<|pad|>", "<|eos|>"]

class TestVocabInfo:
    def test_serialization_roundtrip(self):
        info = VocabInfo(
            vocabSize=32000,
            specialTokenIds={"<|endoftext|>": 0, "<|pad|>": 1},
            compressionRatio=3.8,
            oovRate=0.001,
            trainedAt=datetime(2024, 1, 1, 12, 0, 0),
            configHash="abc123"
        )
        jsonStr = info.to_json()
        restored = VocabInfo.from_json(jsonStr)
        assert restored.vocabSize == info.vocabSize
        assert restored.compressionRatio == info.compressionRatio
        assert restored.trainedAt == info.trainedAt
```

### Services (Logique Métier, Repositories Mockés)

```python
# tests/unit/test_services/test_tokenizerService.py
import pytest
from unittest.mock import MagicMock, patch
from apps.modules.tokenizer.services.tokenizerService import TokenizerService
from apps.modules.tokenizer.models.tokenizerModel import TokenizerConfig, VocabInfo

class TestTokenizerService:
    @pytest.fixture
    def service(self, mockTokenizerRepo, mockCorpusRepo, mockJobRepo, mockWorkerPool):
        trainer = MagicMock()
        encoder = MagicMock()
        return TokenizerService(trainer, encoder, mockTokenizerRepo, mockCorpusRepo, mockJobRepo, mockWorkerPool)
    
    def test_trainTokenizer_createsJob_andSubmitsToWorker(self, service, mockJobRepo, mockWorkerPool):
        config = TokenizerConfig(vocabSize=1000)
        vocabInfo = VocabInfo(vocabSize=1000, specialTokenIds={}, compressionRatio=3.5, oovRate=0.0, 
                              trainedAt=datetime.utcnow(), configHash="abc")
        service._trainer.train.return_value = vocabInfo
        
        job = service.trainTokenizer(config, corpusSampleSize=1000)
        
        assert job.type == JobType.TOKENIZER_TRAINING
        assert job.status == JobStatus.PENDING
        mockJobRepo.save.assert_called_once()
        mockWorkerPool.submit.assert_called_once()
    
    def test_trainTokenizer_savesTokenizerOnSuccess(self, service, mockTokenizerRepo):
        config = TokenizerConfig()
        vocabInfo = VocabInfo(vocabSize=32000, specialTokenIds={}, compressionRatio=3.5, oovRate=0.0,
                              trainedAt=datetime.utcnow(), configHash="abc")
        service._trainer.train.return_value = vocabInfo
        
        job = service.trainTokenizer(config)
        
        # Simule exécution worker
        service._runTokenizerTraining(job.id, 1000)
        
        mockTokenizerRepo.save.assert_called_once()
        assert job.status == JobStatus.COMPLETED
        assert job.result == vocabInfo
```

### ML Components (PyTorch)

```python
# tests/unit/test_ml/test_transformer.py
import torch
import pytest
from apps.modules.model.ml.transformer import TransformerLM, TransformerBlock
from apps.modules.model.models.modelModel import ModelConfig

class TestTransformerLM:
    @pytest.fixture
    def config(self):
        return ModelConfig(
            vocabSize=1000,
            maxSeqLen=64,
            nLayers=2,
            nHeads=4,
            dim=128,
            nKvHeads=2,
            dtype="fp32",
            useRoPE=True,
            compileModel=False
        )
    
    def test_forward_shape(self, config):
        model = TransformerLM(config)
        batch, seq = 2, 32
        inputIds = torch.randint(0, config.vocabSize, (batch, seq))
        
        logits, loss = model(inputIds)
        
        assert logits.shape == (batch, seq, config.vocabSize)
        assert loss is None
    
    def test_forward_with_targets(self, config):
        model = TransformerLM(config)
        batch, seq = 2, 32
        inputIds = torch.randint(0, config.vocabSize, (batch, seq))
        targets = torch.randint(0, config.vocabSize, (batch, seq))
        
        logits, loss = model(inputIds, targets)
        
        assert loss is not None
        assert loss.item() > 0
    
    def test_generate_shape(self, config):
        model = TransformerLM(config)
        model.eval()
        inputIds = torch.randint(0, config.vocabSize, (1, 10))
        
        from apps.modules.model.ml.sampler import Sampler
        sampler = Sampler(temperature=1.0, topK=50, eosTokenId=0)
        
        with torch.inference_mode():
            output = model.generate(inputIds, 20, sampler)
        
        assert output.shape == (1, 30)  # 10 + 20
    
    def test_rope_different_seq_lens(self, config):
        """Teste que RoPE fonctionne pour différentes longueurs."""
        model = TransformerLM(config)
        model.eval()
        
        for seqLen in [1, 16, 32, 64]:
            inputIds = torch.randint(0, config.vocabSize, (1, seqLen))
            with torch.inference_mode():
                logits, _ = model(inputIds)
            assert logits.shape == (1, seqLen, config.vocabSize)
```

### Pipelines Données

```python
# tests/unit/test_pipelines/test_deduplicator.py
import pytest
from apps.modules.corpus.pipelines.deduplicator import Deduplicator
from apps.modules.corpus.models.corpusModel import CleanDocument

class TestDeduplicator:
    @pytest.fixture
    def dedup(self):
        return Deduplicator(exactDedup=True, minhashDedup=True, minhashThreshold=0.7)
    
    def test_exact_deduplication(self, dedup):
        docs = [
            CleanDocument(id="1", source="wiki", language="fr", text="Bonjour monde", qualityScore=0.9, tokenCount=3, cleanedAt=datetime.utcnow()),
            CleanDocument(id="2", source="wiki", language="fr", text="Bonjour monde", qualityScore=0.8, tokenCount=3, cleanedAt=datetime.utcnow()),  # Duplicate
            CleanDocument(id="3", source="wiki", language="fr", text="Au revoir", qualityScore=0.9, tokenCount=2, cleanedAt=datetime.utcnow()),
        ]
        
        result = dedup.deduplicate(docs)
        
        assert len(result) == 2
        assert result[0].id == "1"
        assert result[1].id == "3"
    
    def test_near_deduplication_minhash(self, dedup):
        docs = [
            CleanDocument(id="1", source="wiki", language="fr", text="Le chat mange la souris", qualityScore=0.9, tokenCount=6, cleanedAt=datetime.utcnow()),
            CleanDocument(id="2", source="wiki", language="fr", text="Le chat mange une souris", qualityScore=0.8, tokenCount=6, cleanedAt=datetime.utcnow()),  # Near-dup
            CleanDocument(id="3", source="wiki", language="fr", text="Le chien court vite", qualityScore=0.9, tokenCount=5, cleanedAt=datetime.utcnow()),
        ]
        
        result = dedup.deduplicate(docs)
        
        # Selon threshold, peut garder les 2 ou dédupliquer
        assert len(result) <= 2
```

---

## 5. Tests d'Intégration

```python
# tests/integration/test_api/test_trainingController.py
import pytest
from flask.testing import FlaskClient
from apps import createApp
from apps.shared.config import Settings

class TestTrainingController:
    @pytest.fixture
    def app(self):
        config = Settings(APP_ENV="testing")
        app = createApp(config)
        app.config["TESTING"] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        return app.test_client()
    
    @pytest.fixture
    def authHeaders(self):
        return {"Authorization": "Bearer test-token"}
    
    def test_startTraining_returns202_andJob(self, client, authHeaders, mockServices):
        payload = {
            "modelConfig": {"preset": "125M"},
            "trainShards": ["data/shards/train_000001.bin"],
            "valShards": ["data/shards/val_000001.bin"],
            "batchSize": 16,
            "maxSteps": 1000
        }
        
        response = client.post("/api/training/jobs", json=payload, headers=authHeaders)
        
        assert response.status_code == 202
        data = response.get_json()
        assert "jobId" in data
        assert data["status"] == "pending"
    
    def test_startTraining_requiresAuth(self, client):
        payload = {"modelConfig": {"preset": "125M"}}
        response = client.post("/api/training/jobs", json=payload)
        assert response.status_code == 401
    
    def test_getTrainingJob_returnsDetails(self, client, authHeaders, mockServices):
        # Setup: job exists
        job = mockServices["jobRepo"].findById.return_value
        
        response = client.get("/api/training/jobs/test-job-id", headers=authHeaders)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["jobId"] == "test-job-id"
```

---

## 6. Tests E2E (Playwright)

```typescript
// tests/e2e/test_chat_ui.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Chat Interface', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/chat');
    await page.waitForSelector('[data-testid="chat-interface"]');
  });

  test('should send message and receive streaming response', async ({ page }) => {
    // Type message
    await page.fill('[data-testid="chat-input"]', 'Bonjour, comment ça va ?');
    await page.click('[data-testid="send-button"]');
    
    // User message appears
    await expect(page.locator('[data-testid="message-user"]').last()).toContainText('Bonjour');
    
    // Assistant response streams
    await expect(page.locator('[data-testid="message-assistant"]').last()).toBeVisible();
    
    // Wait for streaming to complete (cursor disappears)
    await expect(page.locator('.animate-pulse')).toBeHidden({ timeout: 10000 });
    
    // Response has content
    const responseText = await page.locator('[data-testid="message-assistant"]').last().textContent();
    expect(responseText.length).toBeGreaterThan(0);
  });

  test('should create new session', async ({ page }) => {
    await page.click('[data-testid="new-session-button"]');
    await expect(page.locator('[data-testid="session-title"]')).toContainText('Nouvelle conversation');
  });

  test('should select model from dropdown', async ({ page }) => {
    await page.click('[data-testid="model-selector"]');
    await page.click('[data-testid="model-option-125M"]');
    await expect(page.locator('[data-testid="model-selector"]')).toContainText('125M');
  });
});
```

---

## 7. Qualité Code (Lint, Type-check, Format)

### Backend (Python)

```toml
# pyproject.toml
[tool.ruff]
target-version = "py311"
line-length = 100
select = [
    "E", "F", "W", "I", "N", "UP", "B", "C4", "DTZ", "T10", "ICN", "PIE", "PT", "Q", "RSE", "SIM", "TID", "TRY"
]
ignore = ["E501"]  # Line length handled by formatter
per-file-ignores = {"tests/*": ["S101", "S106"]}

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
strict_equality = true
```

### Frontend (TypeScript)

```json
// web/tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

```json
// web/.eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended-type-checked",
    "plugin:react-hooks/recommended"
  ],
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

---

## 8. Critères d'Acceptation Globaux

| Domaine | Critère | Seuil | Validation |
|---------|---------|-------|------------|
| **Couverture** | Unit tests | ≥ 85% | `pytest --cov-fail-under=85` |
| | Integration | ≥ 70% | `pytest -m integration --cov-fail-under=70` |
| | E2E | 10 chemins critiques | Playwright CI pass |
| **Performance** | Training throughput | > 50k tok/s/GPU (125M) | Benchmark CI |
| | Inference latency P95 | < 2s first token | Load test |
| | Streaming tokens/sec | > 20 tok/s | WS test |
| | API P99 latency | < 500ms | Locust/k6 |
| **Qualité** | Ruff | 0 erreurs | `ruff check` |
| | MyPy | 0 erreurs | `mypy apps/` |
| | ESLint | 0 erreurs | `npm run lint` |
| | TSC | 0 erreurs | `npx tsc -b` |
| **Reproductibilité** | Checkpoint resume | Bit-exact loss | Test automatisé |
| | Tokenizer determinism | Byte-identical | Hash comparison |
| | Seed fixed | Same results | Fixed seed test |
| **Sécurité** | Path traversal | Bloqué | Test injection |
| | Auth required | 401 sans token | Test API |
| | Rate limit | Appliqué | Test charge |
| **Accessibilité** | WCAG 2.1 AA | Pass | axe-core CI |
| | Keyboard nav | Complete | Test manuel |

---

## 9. Commandes CI Locales

```bash
# Backend
cd D:\Project\riah_code
ruff check apps/ tests/
ruff format --check apps/ tests/
mypy apps/
pytest -m "unit" --cov=apps --cov-fail-under=85
pytest -m "integration"
pytest -m "e2e"  # Requiert stack complet

# Frontend
cd web
npm run lint
npx tsc -b
npm run build
npm run test  # Vitest/Jest
npx playwright test

# Full CI simulation
docker-compose -f docker/docker-compose.yml up --build -d
# Wait for services
pytest -m "integration"
npx playwright test
docker-compose -f docker/docker-compose.yml down
```

---

## 10. Definition of Done (Par Feature)

Une feature est "Done" quand :
- [ ] Code implémenté selon CODING_RULES.md (camelCase, OOP, DDD modules)
- [ ] Types stricts (MyPy clean, TSC clean)
- [ ] Tests unitaires ≥ 85% couverture sur le module
- [ ] Tests d'intégration pour APIs exposées
- [ ] Documentation PRD mise à jour
- [ ] Storybook stories pour composants UI (si frontend)
- [ ] Pas de régression (CI verte)
- [ ] Revu par au moins 1 personne (PR approved)
- [ ] Déployé en staging sans erreur