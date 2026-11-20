# Security Command

## Modèle de commande
**Nom** : `security`  
**Paramètre** : aucun (analyse tout le code)  
**Alias** : aucun

## Objectif
Analyser la sécurité du code et vérifier qu'il n'y a pas de faille. Auditer le code en entier.

## Vérifications à effectuer (dans l'ordre)

1. **Secrets en dur** : chercher `SECRET_KEY`, `PASSWORD`, `API_KEY`, `TOKEN` en dur dans le code
2. **Injections SQL** : chercher les requêtes construites avec f-string ou concaténation de chaînes
3. **Traversée de chemin** : chercher `../` dans les chemins de fichiers (Directory Traversal / Path Traversal)
4. **Fonctions dangereuses** : chercher `eval()`, `exec()`, `pickle`, `cPickle`, `os.system()`, `subprocess.call()` avec `shell=True`
5. **Mode debug en production** : vérifier que `debug=True` n'est pas activé en production
6. **CORS mal configuré** : vérifier les origines autorisées (ne pas accepter `*` en production)
7. **Rate limiting absent** : vérifier que les endpoints sensibles sont protégés contre les abus
8. **Validation d'entrée manquante** : vérifier que tous les endpoints valident leurs inputs avant traitement

## Outils recommandés

- `bandit` pour l'analyse statique de sécurité Python
- `grep` manuel pour les patterns spécifiques
- Revue manuelle du code par l'agent

## Résultat attendu

Un rapport de sécurité listant :
- Chaque vulnérabilité trouvée avec son fichier et ligne
- Le niveau de criticité (low / medium / high / critical)
- La recommandation de correction pour chaque problème

---

## Exemple d'utilisation

```
security
```
