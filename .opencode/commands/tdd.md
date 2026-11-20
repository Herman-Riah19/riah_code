# TDD Command

## Modèle de commande
**Nom** : `tdd`  
**Paramètre requis** : `--module <nom_module>` (ex: `--module users`, `--module corpus`, `--module tokenizer`)  
**Alias** : aucun

## Objectif
Appliquer le Test Driven Development (Développement Piloté par les Tests) : écrire les tests AVANT le code d'implémentation.

## Étapes à suivre (dans l'ordre)

### Phase 1 : Écrire les tests d'abord (AVANT tout code)

1. Créer le fichier de test dans `tests/unit/test_<nom>/test_<nom>.py`
2. **Données valides (compatibles)** : tester que le code accepte les bonnes données
3. **Données invalides (incompatibles)** : tester que le code rejette les mauvaises données (piéger le code)
4. Tester chaque opération CRUD : create, findById, findAll, update, delete
5. Tester les cas limites : id inexistant, nom vide, nom trop long, etc.

### Phase 2 : Faire tourner les tests (ils doivent échouer)

- Les tests doivent échouer car le code d'implémentation n'existe pas encore

### Phase 3 : Écrire le code d'implémentation

- Créer le Model, Repository, Service, Controller pour faire passer les tests
- Un test à la fois

### Phase 4 : Refaire tourner les tests

- Tous les tests doivent passer
- Refactor si nécessaire sans casser les tests

## Règles

- Chaque test se trouve dans le dossier `tests/` du module concerné
- Les tests utilisent `pytest`
- Pas d'implémentation avant que les tests soient écrits
- Les données invalides doivent faire lever des exceptions appropriées

## Résultat attendu

Une suite de tests complète pour le module, avec :
- Tests de données valides qui passent
- Tests de données invalides qui échouent (avant implémentation)
- Code d'implémentation qui fait passer tous les tests

---

## Exemple d'utilisation

```
tdd --module users
tdd --module corpus
tdd --module tokenizer