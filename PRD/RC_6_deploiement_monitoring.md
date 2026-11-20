# RC_6 — Déploiement, Migration & Monitoring

## 1. Objectifs

- **Containerisation** : Docker multi-stage (dev, prod, GPU)
- **Orchestration** : Docker Compose (local), Kubernetes (prod futur)
- **Migration données** : Scripts versionnés pour évolutions schémas
- **Monitoring** : Métriques Prometheus, logs structurés, alerting
- **Sauvegarde** : Stratégie backup/restore artefacts + DB

---

## 2. Structure Déploiement

```
riah_code/
├── docker/
│   ├── Dockerfile.backend       # Multi-stage: builder → runtime
│   ├── Dockerfile.frontend      # Vite build → Nginx
│   ├── docker-compose.yml       # Local dev (CPU)
│   ├── docker-compose.gpu.yml   # Local dev (GPU)
│   └── docker-compose.prod.yml  # Production
├── k8s/                         # Futur Kubernetes
│   ├── base/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   └── secret.yaml
│   ├── overlays/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── prod/
│   └── kustomization.yaml
├── scripts/
│   ├── migrate.py               # Migrations données (Alembic-like custom)
│   ├── backup.py                # Backup artefacts + SQLite
│   ├── restore.py               # Restore depuis backup
│   └── healthcheck.py           # Health checks complets
├── monitoring/
│   ├── prometheus.yml           # Config scrape
│   ├── alert_rules.yml          # Règles alerting
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   ├── training.json
│   │   │   ├── inference.json
│   │   │   └── system.json
│   │   └── datasources.yaml
│   └── loki-config.yml          # Logs aggregation
└── .github/workflows/
    ├── ci.yml                   # Lint, type-check, tests
    ├── build.yml                # Build & push images
    └── deploy.yml               # Deploy staging/prod
```

---

## 3. Docker Multi-Stage

### `Dockerfile.backend`

```dockerfile
# docker/Dockerfile.backend
# ===== BUILDER =====
FROM python:3.11-slim AS builder

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only=main --no-interaction

# ===== RUNTIME =====
FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender-dev libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# App code
COPY apps/ ./apps/
COPY PRD/ ./PRD/
COPY run.py ./

# Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Env
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python scripts/healthcheck.py

CMD ["python", "run.py"]
```

### `Dockerfile.frontend`

```dockerfile
# docker/Dockerfile.frontend
# ===== BUILDER =====
FROM node:20-alpine AS builder

WORKDIR /app

COPY web/package*.json ./
RUN npm ci --legacy-peer-deps

COPY web/ ./
RUN npm run build

# ===== RUNTIME =====
FROM nginx:alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

### `docker-compose.yml` (Local CPU)

```yaml
# docker/docker-compose.yml
version: "3.9"

services:
  backend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.backend
      target: runtime
    volumes:
      - ../data:/app/data
      - ../logs:/app/logs
    environment:
      - APP_ENV=development
      - DATABASE_URL=sqlite:///data/app.db
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "5000:5000"
    depends_on:
      - redis
    deploy:
      resources:
        limits:
          memory: 4G
  
  backend-gpu:
    profiles: ["gpu"]
    build:
      context: ..
      dockerfile: docker/Dockerfile.backend
      target: runtime
    volumes:
      - ../data:/app/data
      - ../logs:/app/logs
    environment:
      - APP_ENV=development
      - DATABASE_URL=sqlite:///data/app.db
      - CUDA_VISIBLE_DEVICES=0
    ports:
      - "5001:5000"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    depends_on:
      - redis
  
  frontend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.frontend
      target: runtime
    ports:
      - "3000:80"
    depends_on:
      - backend
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ../monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    volumes:
      - ../monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ../monitoring/grafana/datasources.yaml:/etc/grafana/provisioning/datasources/datasources.yaml
      - grafana_data:/var/lib/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  redis_data:
  prometheus_data:
  grafana_data:
```

---

## 4. Migrations Données (`scripts/migrate.py`)

```python
# scripts/migrate.py
"""
Système de migration versionné pour schémas SQLite + artefacts.
Chaque migration = classe avec up()/down(), version timestampée.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sqlite3, json, importlib, inspect

@dataclass
class Migration:
    version: str           # "20241201_001_initial_schema"
    description: str
    up: callable           # fn(conn) -> None
    down: callable         # fn(conn) -> None

class MigrationRunner:
    def __init__(self, dbPath: Path, migrationsModule: str = "migrations"):
        self._dbPath = dbPath
        self._migrationsModule = migrationsModule
        self._initSchemaTable()
    
    def _initSchemaTable(self):
        with sqlite3.connect(self._dbPath) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    description TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def getAppliedVersions(self) -> set[str]:
        with sqlite3.connect(self._dbPath) as conn:
            return {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
    
    def discoverMigrations(self) -> list[Migration]:
        module = importlib.import_module(self._migrationsModule)
        migrations = []
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, BaseMigration) and obj != BaseMigration:
                migration = obj()
                migrations.append(Migration(
                    version=migration.version,
                    description=migration.description,
                    up=migration.up,
                    down=migration.down
                ))
        return sorted(migrations, key=lambda m: m.version)
    
    def migrate(self, targetVersion: str | None = None) -> list[str]:
        applied = self.getAppliedVersions()
        allMigrations = self.discoverMigrations()
        pending = [m for m in allMigrations if m.version not in applied]
        
        if targetVersion:
            pending = [m for m in pending if m.version <= targetVersion]
        
        appliedVersions = []
        with sqlite3.connect(self._dbPath) as conn:
            for migration in pending:
                print(f"Applying {migration.version}: {migration.description}")
                migration.up(conn)
                conn.execute(
                    "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                    (migration.version, migration.description)
                )
                appliedVersions.append(migration.version)
        return appliedVersions
    
    def rollback(self, targetVersion: str) -> list[str]:
        applied = self.getAppliedVersions()
        allMigrations = self.discoverMigrations()
        toRollback = [m for m in reversed(allMigrations) if m.version in applied and m.version > targetVersion]
        
        rolledBack = []
        with sqlite3.connect(self._dbPath) as conn:
            for migration in toRollback:
                print(f"Rolling back {migration.version}")
                migration.down(conn)
                conn.execute("DELETE FROM schema_migrations WHERE version = ?", (migration.version,))
                rolledBack.append(migration.version)
        return rolledBack

# Exemple migration
# migrations/20241201_001_initial_schema.py
class BaseMigration(ABC):
    @property
    @abstractmethod
    def version(self) -> str: ...
    @property
    @abstractmethod
    def description(self) -> str: ...
    @abstractmethod
    def up(self, conn: sqlite3.Connection) -> None: ...
    @abstractmethod
    def down(self, conn: sqlite3.Connection) -> None: ...

class Migration_20241201_001_initial_schema(BaseMigration):
    version = "20241201_001_initial_schema"
    description = "Create initial tables: jobs, checkpoints, chat_sessions"
    
    def up(self, conn):
        conn.executescript("""
            CREATE TABLE jobs (...);
            CREATE TABLE checkpoints (...);
            CREATE TABLE chat_sessions (...);
            CREATE TABLE chat_messages (...);
        """)
    
    def down(self, conn):
        conn.executescript("DROP TABLE IF EXISTS jobs, checkpoints, chat_sessions, chat_messages;")
```

---

## 5. Monitoring & Observabilité

### Métriques Prometheus (exposées par `/metrics`)

```python
# apps/shared/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Summary

# HTTP
HTTP_REQUESTS_TOTAL = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
HTTP_REQUEST_DURATION = Histogram("http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"])

# Jobs
JOB_STARTED = Counter("jobs_started_total", "Jobs started", ["type"])
JOB_COMPLETED = Counter("jobs_completed_total", "Jobs completed", ["type", "status"])
JOB_DURATION = Histogram("job_duration_seconds", "Job duration", ["type"])

# Training
TRAINING_STEP = Counter("training_step_total", "Training steps completed")
TRAINING_LOSS = Gauge("training_loss", "Current training loss")
TRAINING_LR = Gauge("training_learning_rate", "Current learning rate")
TRAINING_TOKENS_PER_SEC = Gauge("training_tokens_per_sec", "Throughput")
GPU_MEMORY_USED = Gauge("gpu_memory_used_bytes", "GPU memory used", ["device"])
GPU_UTILIZATION = Gauge("gpu_utilization_percent", "GPU utilization", ["device"])

# Inference
INFERENCE_REQUESTS = Counter("inference_requests_total", "Inference requests", ["model", "status"])
INFERENCE_LATENCY = Histogram("inference_latency_seconds", "Inference latency", ["model"])
INFERENCE_TOKENS_PER_SEC = Gauge("inference_tokens_per_sec", "Generation throughput", ["model"])
MODEL_LOADED = Gauge("model_loaded", "Model currently loaded", ["checkpoint_id"])

# Chat
CHAT_SESSIONS_ACTIVE = Gauge("chat_sessions_active", "Active chat sessions")
CHAT_MESSAGES_TOTAL = Counter("chat_messages_total", "Messages sent", ["role"])
WS_CONNECTIONS = Gauge("websocket_connections_active", "Active WebSocket connections")
```

### Règles Alerte (`monitoring/alert_rules.yml`)

```yaml
groups:
- name: riah-code
  rules:
  - alert: HighTrainingLoss
    expr: training_loss > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Training loss elevated ({{ $value }})"
  
  - alert: TrainingStalled
    expr: rate(training_step_total[10m]) == 0
    for: 10m
    labels:
      severity: critical
    annotations:
      summary: "Training appears stalled"
  
  - alert: GPUOOMRisk
    expr: gpu_memory_used_bytes / gpu_memory_total_bytes > 0.95
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "GPU memory > 95% on {{ $labels.device }}"
  
  - alert: InferenceHighLatency
    expr: histogram_quantile(0.95, rate(inference_latency_seconds_bucket[5m])) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "P95 inference latency > 10s"
  
  - alert: DiskSpaceLow
    expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Disk space < 10% on {{ $labels.instance }}"
```

### Dashboards Grafana (JSON)

- **Training Dashboard** : Loss curve, LR schedule, throughput, GPU mem/util, step time
- **Inference Dashboard** : Latency P50/P95/P99, tokens/sec, queue depth, cache hit rate
- **System Dashboard** : CPU, RAM, Disk, Network, Container health

---

## 6. Backup & Restore (`scripts/backup.py`, `scripts/restore.py`)

```python
# scripts/backup.py
class BackupManager:
    def __init__(self, dataDir: Path, backupDir: Path):
        self._dataDir = dataDir
        self._backupDir = backupDir
    
    def createBackup(self, name: str | None = None) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backupName = name or f"backup_{timestamp}"
        backupPath = self._backupDir / backupName
        backupPath.mkdir(parents=True)
        
        # 1. SQLite databases
        for db in self._dataDir.rglob("*.sqlite"):
            rel = db.relative_to(self._dataDir)
            dest = backupPath / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            self._backupSqlite(db, dest)
        
        # 2. Checkpoints (méta seulement, pas les gros .pt)
        checkpointsDir = self._dataDir / "checkpoints"
        if checkpointsDir.exists():
            metaDir = backupPath / "checkpoints_meta"
            metaDir.mkdir()
            for ckpt in checkpointsDir.glob("*.pt"):
                # Sauvegarde seulement métadonnées (sans weights)
                meta = self._extractCheckpointMeta(ckpt)
                (metaDir / f"{ckpt.stem}.json").write_text(json.dumps(meta))
        
        # 3. Tokenizer
        tokenizerDir = self._dataDir / "tokenizer"
        if tokenizerDir.exists():
            shutil.copytree(tokenizerDir, backupPath / "tokenizer")
        
        # 4. Corpus index (pas les shards .bin)
        corpusIndex = self._dataDir / "corpus" / "corpus_index.sqlite"
        if corpusIndex.exists():
            shutil.copy2(corpusIndex, backupPath / "corpus_index.sqlite")
        
        # 5. Manifest
        manifest = {
            "createdAt": datetime.utcnow().isoformat(),
            "version": "1.0",
            "dataDir": str(self._dataDir),
            "includes": ["sqlite", "tokenizer", "checkpoint_meta", "corpus_index"]
        }
        (backupPath / "manifest.json").write_text(json.dumps(manifest))
        
        return backupPath
    
    def _backupSqlite(self, src: Path, dest: Path):
        # Backup cohérent avec .backup API
        import sqlite3
        srcConn = sqlite3.connect(src)
        destConn = sqlite3.connect(dest)
        srcConn.backup(destConn)
        srcConn.close()
        destConn.close()
```

---

## 7. CI/CD GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  lint-typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - name: Install deps
        run: |
          pip install -e ".[dev]"
          pip install ruff mypy
      - name: Ruff lint
        run: ruff check apps/ tests/
      - name: MyPy type check
        run: mypy apps/
  
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - name: Install deps
        run: pip install -e ".[dev,test]"
      - name: Run tests
        run: pytest --cov=apps --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
  
  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - name: Install deps
        run: cd web && npm ci --legacy-peer-deps
      - name: ESLint
        run: cd web && npm run lint
      - name: TypeScript build
        run: cd web && npx tsc -b
      - name: Build
        run: cd web && npm run build

---
# .github/workflows/build.yml
name: Build & Push

on:
  push:
    tags: ["v*"]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Build & push backend
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile.backend
          push: true
          tags: ghcr.io/${{ github.repository }}/backend:${{ github.ref_name }}
  
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Build & push frontend
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile.frontend
          push: true
          tags: ghcr.io/${{ github.repository }}/frontend:${{ github.ref_name }}
```

---

## 8. Checklist Production

| Élément | Status |
|---------|--------|
| Docker images multi-arch (amd64/arm64) | ☐ |
| Secrets management (Vault/SealedSecrets) | ☐ |
| TLS termination (cert-manager + Let's Encrypt) | ☐ |
| Rate limiting (nginx/Traefik) | ☐ |
| Log rotation (Loki + retention) | ☐ |
| Backup schedule (cron + offsite) | ☐ |
| Disaster recovery test (trimestriel) | ☐ |
| Capacity planning (GPU, storage) | ☐ |