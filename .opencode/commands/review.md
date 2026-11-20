# Review Command

## Modèle de commande
**Nom** : `review`  
**Paramètre** : aucun (revue du code actuel)  
**Alias** : aucun

## Objectif
Faire une revue de code complète avant tout commit. Informer l'utilisateur de tout ce que le code fait.

## Étapes à suivre (dans l'ordre)

### 1. Supprimer les imports inutilisés
- Identifier tous les imports non utilisés (ruff F401)
- Les supprimer de chaque fichier

### 2. Supprimer les fonctions inutilisées
- Identifier toutes les fonctions qui ne sont appelées nulle part
- Les supprimer

### 3. Vérifier le linter
- Lancer `ruff check apps/ tests/`
- 0 erreur requise

### 4. Vérifier le formatage
- Lancer `ruff format --check apps/ tests/`
- Corriger tous les problèmes de formatage

### 5. Vérifier le typage
- Lancer `mypy apps/`
- 0 erreur requise

### 6. Vérifier le respect des CODING_RULES.md
- **camelCase** pour fonctions et variables (pas de snake_case)
- **UPPER_SNAKE_CASE** pour constantes
- **Pas de balise HTML primitive** dans le frontend (utiliser les atomes du design system)
- **Décorateurs = seules fonctions autorisées** hors classes (dans `apps/modules/shared/decorators/`)
- **Pas de code fonctionnel hors des classes** (sauf décorateurs)

### 7. Avant tout commit - Informer l'utilisateur
L'utilisateur doit être informé de :
- **Ce que le code fait** (fonctionnalités implémentées)
- **Quels fichiers** ont été créés, modifiés ou supprimés
- **Que toutes les vérifications sont passées** (lint, format, type-check, aucun import inutilisé)
- **Que le code respecte les CODING_RULES.md**

## Résultat attendu

Un rapport de revue listant :
- Fichiers modifiés
- Erreurs trouvées et corrigées
- Confirmation que toutes les vérifications passent
- Résumé de ce que le code fait

---

## Exemple d'utilisation

```
review
```
