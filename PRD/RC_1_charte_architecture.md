# RC_1 — Charte du Projet & Architecture Globale

## 1. Vision & Objectifs

**Riah Code** est une plateforme complète pour créer, entraîner et servir son propre modèle de langage (LLM) from scratch, avec :
- **Backend** : Pipeline de données → Tokenizer → Modèle Transformer → Entraînement → Inférence (API REST + WebSocket)
- **Frontend** : Interface de chat type ChatGPT (React 19, Tailwind v4, Design System Atomic)
- **Données** : Scraping web (Wikipedia, plateformes bibliques, sources ouvertes) → Corpus nettoyé → Tokenizer BPE → Entraînement

### Objectifs Produit
1. **Autonomie totale** : Pas de dépendance à des modèles pré-entraînés externes (Hugging Face, OpenAI, etc.)
2. **Reproductibilité** : Seed fixe, configuration versionnée, artefacts traçables
3. **Extensibilité** : Architecture modulaire (Model-Service-Controller + Repository) pour swaper composants
4. **Observabilité** : Logs structurés, métriques temps réel, dashboard d'entraînement
5. **Sécurité données** : Pas de fuite PII, contrôle d'accès, purge configurable

---

## 2. Architecture Cible (Alignée CODING_RULES.md)

```
apps/
├── controllers/       # Couche HTTP (Flask Blueprints) + WebSocket
│   ├── chatController.py
│   ├── trainingController.py
│   ├── dataController.py
│   └── healthController.py
├── decorators/        # Seules fonctions autorisées hors classes
│   ├── auth.py
│   ├── validation.py
│   ├── retry.py
│   ├── logging.py
│   └── rateLimit.py
├── models/            # Entités de domaine (dataclass frozen / Pydantic)
│   ├── corpus.py
│   ├── tokenizer.py
│   ├── model.py
│   ├── training.py
│   ├── checkpoint.py
│   └── chat.py
├── repositories/      # Abstraction stockage (FS, SQLite, S3, HF Hub)
│   ├── corpusRepository.py
│   ├── tokenizerRepository.py
│   ├── checkpointRepository.py
│   ├── metricsRepository.py
│   └── chatRepository.py
├── services/          # Logique métier pure, injection de repositories
│   ├── scrapingService.py
│   ├── corpusService.py
│   ├── tokenizerService.py
│   ├── trainingService.py
│   ├── inferenceService.py
│   └── chatService.py
├── ml/                # Briques ML pures (réutilisables CLI + API)
│   ├── transformer.py
│   ├── attention.py
│   ├── feedForward.py
│   ├── tokenizer.py
│   ├── sampler.py
│   └── loss.py
├── pipelines/         # Pipelines de données (classes pures)
│   ├── wikiScraper.py
│   ├── bibleScraper.py
│   ├── htmlCleaner.py
│   ├── textNormalizer.py
│   ├── deduplicator.py
│   └── shardWriter.py
├── storage/           # Utilitaires bas niveau (FS, DB, Cloud)
│   ├── fileStorage.py
│   ├── sqliteStorage.py
│   └── s3Storage.py
├── config.py          # Configuration par environnement (Pydantic Settings)
└── __init__.py        # Application factory (createApp)
```

### Principes Architecturaux
| Couche | Responsabilité | Exemple |
|--------|----------------|---------|
| **Controller** | HTTP only : validation request → délégation Service → réponse JSON | `chatController.sendMessage()` |
| **Service** | Logique métier, orchestration, règles de gestion | `trainingService.startTraining()` |
| **Repository** | Seul accès au stockage (CRUD, requêtes) | `checkpointRepository.save()` |
| **Model** | Entité immuable, sérialisation, validation | `TrainingConfig`, `Checkpoint` |
| **ML/Pipeline** | Classes pures, sans I/O, testables unitairement | `Transformer.forward()`, `WikiScraper.scrape()` |

---

## 3. Décisions Techniques Majeures (Figées)

| Sujet | Décision | Justification |
|-------|----------|---------------|
| **Architecture Modèle** | Transformer Decoder-only (style GPT-2) | Standard éprouvé, parallélisable, compatible checkpoints |
| **Tokenizer** | BPE (Byte Pair Encoding) entraîné sur corpus cible | Vocabulaire adapté aux données, pas de mismatch token/modèle |
| **Vocabulaire** | 32 000 tokens (configurable) | Équilibre compression/performance pour français/anglais |
| **Données** | Wikipedia (FR/EN) + Bible (multi-langues) + Common Crawl échantillon | Sources ouvertes, qualité, diversité linguistique |
| **Stockage Artefacts** | Fichiers locaux (JSONL, .pt, .bin) + SQLite pour index | Simplicité, pas de dépendance externe, reproductible |
| **Reprise Entraînement** | Checkpoints complets (modèle + optimizer + scheduler + RNG) | Reprise exacte, pas de dérive |
| **Inférence** | `torch.inference_mode()`, KV-cache, streaming tokens | Latence faible, UX chat temps réel |
| **Frontend Chat** | WebSocket pour streaming, Design System Atomic (Tailwind v4) | UX fluide, composants réutilisables |
| **Configuration** | Pydantic Settings (YAML + env vars), validation au démarrage | Type-safe, documented, environment-aware |

---

## 4. Périmètre Fonctionnel (MVP)

### Phase 1 — Données & Tokenizer (RC_2, RC_3)
- [ ] Scraper Wikipedia (API REST + dump) → JSONL brut
- [ ] Scraper plateformes bibliques (API/public HTML) → JSONL brut
- [ ] Nettoyage HTML → texte brut (suppression balises, scripts, pubs)
- [ ] Normalisation Unicode, déduplication (MinHash), filtrage qualité
- [ ] Écriture shards (parquet/JSONL) partitionnés par source/langue
- [ ] Entraînement BPE (32k vocab) → tokenizer.json + vocabulaire
- [ ] Encodage corpus → IDs (uint16) + fichiers `.bin` (memmap)

### Phase 2 — Modèle & Entraînement (RC_4)
- [ ] Transformer Decoder-only (configurable : layers, heads, dim, context)
- [ ] Initialisation poids (GPT-2 style), RoPE ou positions apprises
- [ ] Mixed precision (bf16/fp16), gradient accumulation, gradient clipping
- [ ] Optimizer AdamW + cosine decay + warmup
- [ ] Checkpointing complet (model, opt, sched, RNG, step, epoch)
- [ ] Logging métriques (loss, lr, throughput, GPU mem) → JSONL + TensorBoard
- [ ] Arrêt gracieux (SIGTERM) → checkpoint + flush

### Phase 3 — API & Chat (RC_5)
- [ ] Flask API : `/health`, `/models`, `/chat/completions` (OpenAI-compatible)
- [ ] WebSocket `/ws/chat` pour streaming token-par-token
- [ ] Chargement checkpoint à la demande (lazy, cache LRU)
- [ ] Sampler : temperature, top-k, top-p, repetition penalty, stop sequences
- [ ] Contexte conversation (historique + system prompt) → tokens
- [ ] Frontend React : ChatInterface, MessageBubble, TokenStream, ModelSelector

### Phase 4 — Qualité & Observabilité (RC_7)
- [ ] Tests unitaires (models, services, ML, pipelines)
- [ ] Tests d'intégration (API, training loop, chat flow)
- [ ] Benchmarks : perplexité, throughput, latence P50/P99
- [ ] CI/CD : lint, type-check, tests, build Docker

---

## 5. Contraintes Non-Fonctionnelles

| Contrainte | Exigence |
|------------|----------|
| **Hardware min** | 1 GPU 8GB VRAM (RTX 3070/4060), 16GB RAM, 50GB SSD |
| **Hardware recommandé** | 2× GPU 24GB (RTX 3090/4090), 64GB RAM, NVMe 1TB |
| **OS** | Linux (Ubuntu 22.04+) ou WSL2, CUDA 12.1+ |
| **Python** | 3.11+ (typing, match-case, tomllib) |
| **Dépendances ML** | PyTorch 2.3+, tokenizers, datasets, accelerate |
| **Taille modèle cible** | 125M → 1.3B params (configurable) |
| **Contexte** | 2048 → 8192 tokens (configurable) |
| **Latence chat** | < 100ms/token (streaming), < 2s first token |
| **Disponibilité** | Local-first, pas de SLA cloud |

---

## 6. Critères d'Acceptation Globaux

1. **Données** : > 10GB texte nettoyé, > 95% dédupliqué, tokenizer compression ratio > 3.5
2. **Entraînement** : Loss converge, perplexité < 20 sur validation, checkpoint résumable
3. **Inférence** : Génération cohérente, streaming fluide, API compatible OpenAI
4. **Chat UI** : Streaming temps réel, historique persistant, sélection modèle/checkpoint
5. **Code** : 100% `tsc -b` / `mypy` strict, `pytest` > 80% coverage, `ruff` clean
6. **Documentation** : README, ADR (Architecture Decision Records), API docs (OpenAPI)

---

## 7. Livrables par PRD

| PRD | Fichier | Contenu Principal |
|-----|---------|-------------------|
| RC_1 | `RC_1_charte_architecture.md` | Ce document : vision, archi, décisions, périmètre |
| RC_2 | `RC_2_pipeline_donnees.md` | Scraping, nettoyage, déduplication, sharding, config |
| RC_3 | `RC_3_tokenizer_corpus.md` | BPE training, vocabulaire, encodage, formats fichiers |
| RC_4 | `RC_4_modele_entrainement.md` | Transformer, config, boucle entraînement, checkpoints |
| RC_5 | `RC_5_api_chat_inference.md` | API REST/WS, chat frontend, sampler, chargement modèles |
| RC_6 | `RC_6_architecture_cible_migration.md` | Structure finale, migration, déploiement, monitoring |
| RC_7 | `RC_7_tests_qualite_acceptation.md` | Stratégie tests, benchmarks, critères acceptation, CI |