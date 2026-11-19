# AGENTS.md — Guide de Configuration & Instructions Antigravity

Ce fichier constitue le guide d'instruction principal pour les agents IA (Google Antigravity, Claude, Codex, Gemini) opérant sur le dépôt **Riah Code**.

---

## 1. Vue d'Ensemble du Projet

**Riah Code** est une plateforme complète d'entraînement, de fine-tuning et d'inférence de modèles de langage (Transformers), couplée à un tableau de bord web interactif.

### Architecture Globale
```
d:\Project\riah_code/
├── apps/                 # Backend Python : API Flask, services ML, gestion des runs
│   ├── config.py         # Configurations d'environnement (Debug / Production)
│   └── __init__.py       # Factory Flask (create_app)
├── web/                  # Frontend Web : React 19, Vite, TypeScript, Storybook
│   ├── src/
│   │   ├── components/   # Atomic Design (atoms, molecules, organisms, templates)
│   │   ├── pages/        # Vues du dashboard
│   │   └── ...
│   └── package.json
├── PRD/                  # Spécifications fonctionnelles et techniques détaillées
│   ├── RC_1_cadrage_analyse_existant.md
│   ├── RC_2_pipeline_donnees.md
│   ├── RC_3_tokenizer_et_corpus.md
│   ├── RC_4_modele_et_entrainement.md
│   ├── RC_5_api_dashboard_et_inference.md
│   ├── RC_6_architecture_cible_et_migration.md
│   └── RC_7_tests_qualite_et_acceptation.md
├── run.py                # Point d'entrée de l'application Flask
├── requirement.txt       # Dépendances Python (PyTorch, Flask, Transformers, Datasets)
├── CODING_RULES.md       # Règles de développement du Backend Python & ML
├── AGENTS.md             # Ce fichier (Guide central pour les agents)
└── GEMINI.md             # Miroir d'instructions pour Google Antigravity
```

---

## 2. Commandes Utiles & Environnements

### 2.1. Backend Python
- **Environnement virtuel** : `.venv` à la racine (`d:\Project\riah_code\.venv`)
- **Lancer le serveur Flask** :
  ```bash
  python run.py
  ```
- **Installer les dépendances Python** :
  ```bash
  pip install -r requirement.txt
  ```
- **Lancer les tests** :
  ```bash
  pytest
  ```

### 2.2. Frontend Web
- **Répertoire de travail** : `web/`
- **Lancer le serveur de développement Vite** :
  ```bash
  npm --prefix web run dev
  ```
- **Build de production** :
  ```bash
  npm --prefix web run build
  ```
- **Linter (ESLint)** :
  ```bash
  npm --prefix web run lint
  ```
- **Lancer Storybook** :
  ```bash
  npm --prefix web run storybook
  ```

---

## 3. Règles Impératives pour l'Agent

### 3.1. Règles Frontend (`web/`) — OBLIGATOIRES
Consulter impérativement [`web/CODING_RULES.md`](file:///d:/Project/riah_code/web/CODING_RULES.md).

1. **ZÉRO BALISE HTML PRIMITIVE DANS LES PAGES / COMPOSANTS MÉTIER** :
   - Interdiction d'utiliser directement `<div>`, `<section>`, `<span>`, `<p>`, `<h1>`–`<h6>`, `<button>`, `<input>`, `<ul>`, `<li>`, `<a>`, etc.
   - Tout élément visuel **doit** être composé à partir des Atomes du Design System : `<Box>`, `<Flex>`, `<Stack>`, `<Text>`, `<Heading>`, `<Button>`, etc.
   - Si une balise primitive manque, créer d'abord un Atome réutilisable et générique dans `src/components/atoms/`.
2. **COMPOSANTS GÉNÉRIQUES ET RÉUTILISABLES** :
   - Ne jamais concevoir un composant dédié à une seule page (ex: pas de `DashboardHeader`, mais un `Header` ou `PageHeader` paramétrable par props).
   - Utiliser des variantes typées (`variant`, `size`, `colorScheme`, `isLoading`).
3. **STORYBOOK OBLIGATOIRE (CDD)** :
   - Tout composant dans `atoms/`, `molecules/`, ou `organisms/` doit avoir son fichier `*.stories.tsx` avec documentation des args et états visuels.
4. **ARCHITECTURE ATOMIC DESIGN STRICTE** :
   - `atoms/` → `molecules/` → `organisms/` → `templates/` → `pages/`.

### 3.2. Règles Backend Python (`apps/`) — OBLIGATOIRES
Consulter impérativement [`CODING_RULES.md`](file:///d:/Project/riah_code/CODING_RULES.md).

1. **PEP 8 strict** : `snake_case` pour fonctions et variables, `PascalCase` pour classes.
2. **Typage strict** : Type hints complets (`typing`, Python 3.10+) sur toutes les signatures.
3. **Découplage API / ML** : Pas de code d'entraînement ou d'inférence lourd directement dans les contrôleurs de routes Flask. Passer par des services et des threads/workers supervisés.
4. **Sécurité des chemins** : Valider tout chemin de checkpoint ou fichier pour éviter les failles de Directory Traversal (`Path.is_relative_to`).
5. **Respect des spécifications PRD** : S'aligner sur les contrats de routes et formats JSON définis dans `PRD/RC_5_api_dashboard_et_inference.md`.

---

## 4. Priorités et Procédure de Contribution

Lorsqu'une modification ou une nouvelle fonctionnalité est demandée :
1. **Vérifier l'alignement avec les PRD** dans `PRD/`.
2. **Pour le frontend** :
   - Identifier les Atomes nécessaires. Si un atome manque, le créer avec son Storybook.
   - Assembler les molécules et organismes.
   - Intégrer dans le template puis la page finale sans balises HTML primitives.
   - Vérifier avec `npm --prefix web run build` et `npm --prefix web run lint`.
3. **Pour le backend** :
   - Définir le schéma d'entrée/sortie typé.
   - Implémenter la logique dans le service dédié.
   - Exposer la route Flask dans un Blueprint avec gestion d'erreurs structurée.
   - Vérifier avec `pytest`.
