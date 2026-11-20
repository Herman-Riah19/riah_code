# CRUD Command

## Modèle de commande
**Nom** : `crud`  
**Paramètre requis** : `--name <nom_module>` (ex: `--name users`, `--name products`, `--name trainingJobs`)  
**Alias** : aucun

## Objectif
Créer un module complet avec toutes les opérations CRUD (Create, Read, Update, Delete) selon l'architecture DDD définie dans CODING_RULES.md.

## Étapes à suivre (dans l'ordre)

### 1. Créer le Model (entité de domaine)
Fichier : `apps/modules/<nom>/models/<nom>Model.py`
- Utiliser `@dataclass(frozen=True)`
- Noms en `camelCase`
- Classes : `<Nom>`, `<Nom>Create`, `<Nom>Update`, `<Nom>Response`

### 2. Créer le Repository (CRUD complet)
Fichier : `apps/modules/<nom>/repositories/<nom>Repository.py`
- Méthodes : `create()`, `findById()`, `findAll()`, `update()`, `delete()`, `count()`
- Pas de logique métier, seulement accès aux données

### 3. Créer les schémas de validation (Pydantic)
Fichier : `apps/modules/<nom>/services/<nom>Validation.py`
- Schémas : `<Nom>CreateSchema`, `<Nom>UpdateSchema`, `<Nom>ResponseSchema`
- Validation des données d'entrée

### 4. Créer le Service (logique métier)
Fichier : `apps/modules/<nom>/services/<nom>Service.py`
- Orchestre le Repository et les schémas de validation
- Pas de code HTTP ici

### 5. Créer le Controller (Flask Blueprint)
Fichier : `apps/modules/<nom>/controllers/<nom>Controller.py`
- Routes : POST `/`, GET `/<id>`, GET `/`, PUT `/<id>`, DELETE `/<id>`
- Utilise `@requireAuth` et `@validateInput`
- Le Blueprint est défini en haut du fichier

### 6. Créer le service frontend (TypeScript + Zod)
Fichier : `web/src/features/<nom>/use<Nom>.ts`
- Schémas Zod équivalents aux Pydantic
- Fonctions : `create()`, `get()`, `list()`, `update()`, `remove()`
- Appelle l'API du Controller

## Règles impératives

- **ZÉRO import inutilisé** : chaque import doit être utilisé
- **camelCase uniquement** pour fonctions, variables, paramètres (pas de snake_case)
- **UPPER_SNAKE_CASE** pour constantes
- **Pas de balise HTML primitive** dans le frontend (utiliser les atomes du design system)
- **Décorateurs = seules fonctions autorisées** hors classes (dans `apps/modules/shared/decorators/`)
- **Stockage local uniquement** (pas de S3, pas de cloud)

## Résultat attendu

Un module complet, testable, avec :
- Model → Repository → Service → Controller → Frontend service
- Tous les fichiers ont leur `index.ts` / `__init__.py` avec exports publics
- Aucun code fonctionnel hors des classes (sauf décorateurs)

---

## Exemple d'utilisation

```
crud --name users
crud --name trainingJobs
crud --name checkpoints
```
