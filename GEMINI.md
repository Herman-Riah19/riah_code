# GEMINI.md — Instructions Antigravity pour Riah Code

Ce fichier est découvert et chargé par Google Antigravity. Il pointe vers les guides de référence du projet.

Pour les instructions détaillées complètes, se référer à :
- **Guide Agent Global** : [AGENTS.md](file:///d:/Project/riah_code/AGENTS.md)
- **Règles Backend Python & ML** : [CODING_RULES.md](file:///d:/Project/riah_code/CODING_RULES.md)
- **Règles Frontend React, Atomic Design & Storybook** : [web/CODING_RULES.md](file:///d:/Project/riah_code/web/CODING_RULES.md)

---

## Rappel des Règles Clés pour toute Tâche

1. **Frontend (React / TypeScript)** :
   - **Interdiction formelle des balises HTML primitives** (`div`, `span`, `p`, `button`, etc.) dans les pages et composants fonctionnels.
   - Utilisation exclusive des Atomes du Design System (`Box`, `Flex`, `Stack`, `Text`, `Heading`, `Button`, etc.).
   - Composants 100% réutilisables, paramétrés par props et variantes, jamais personnalisés pour une seule page.
   - Stories Storybook obligatoires pour chaque Atome, Molécule et Organisme (`*.stories.tsx`).
   - Architecture en couches : `atoms` -> `molecules` -> `organisms` -> `templates` -> `pages`.

2. **Backend (Python / Flask / ML)** :
   - Conventions `CODING_RULES.md` : `camelCase` pour fonctions/variables/paramètres, `UPPER_SNAKE_CASE` pour constantes, `PascalCase` pour classes.
   - Typage explicite avec `typing` sur toutes les fonctions et méthodes.
   - Séparation en couches : Contrôleurs de routes, Services applicatifs, Modèles ML, Pipelines de données.
   - Sécurisation absolue des chemins de fichiers et checkpoints (anti-directory traversal).
   - Contrats d'API stables conformes aux spécifications dans `PRD/`.
