# Règle Antigravity : Développement Backend Python & ML

Cette règle s'applique à tous les fichiers Python (`*.py`), scripts ML et configurations backend du projet.

## Standards Obligatoires

1. **PEP 8 & Typage Stricte** :
   - Fonctions et variables en `camel_case`.
   - Classes en `PascalCase`. Constantes en `UPPER_SNAKE_CASE`.
   - Annotations de types complètes (`typing`, Python 3.10+) sur chaque fonction et méthode.
   - Utiliser des `dataclass` ou `Pydantic` pour les schémas de données et configurations.

2. **Architecture en Couches Découplée** :
   - Routes Flask (Blueprints) : uniquement validation des entrées et sérialisation des sorties.
   - Services : logique applicative, orchestration des jobs et gestion du cycle de vie.
   - Modules ML (`apps/ml`, `apps/pipelines`) : modules purs réutilisables par l'API et la CLI.

3. **Jobs Longs & Concurrence** :
   - Les entraînements et préparations doivent tourner dans des workers / threads supervisés avec token d'annulation.
   - Persistance atomique de l'état des jobs et des métriques (fichiers JSONL ou DB).

4. **Sécurité & Chemins de Fichiers** :
   - Ne jamais faire confiance à un chemin envoyé par l'utilisateur.
   - Toujours valider via `Path.resolve().is_relative_to(...)` pour prévenir les attaques de type Directory Traversal.

5. **Gestion des Erreurs** :
   - Réponses d'erreur au format JSON structuré avec code d'erreur applicatif.
   - Pas de `except: pass` silencieux.
