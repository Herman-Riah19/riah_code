# RC_6 — Architecture cible et stratégie de réécriture

## Mission

Transformer les exigences des RC_1 à RC_5 en une architecture testable et un plan de migration progressif, sans choisir prématurément un framework ou une infrastructure.

## Problèmes de structure à résoudre

- Le serveur Flask concentre le routage HTTP, la validation, la gestion d'état, les threads, l'accès aux fichiers, le chargement du modèle et l'orchestration des algorithmes.
- Plusieurs traitements et chemins par défaut sont dupliqués entre les scripts CLI et le serveur.
- L'état des jobs est local au processus ; les threads daemon sont perdus au redémarrage.
- Les frontières entre source, logique métier et stockage sont implicites (constantes de chemins globales).
- Les contrats de configuration / erreurs / états ne sont pas uniformes.
- Le tokenizer BPE et le modèle byte-level ne partagent pas le même contrat d'encodage.

## Cibles de conception à spécifier

Le PRD doit décrire les responsabilités attendues, sans exiger une structure de fichiers particulière :

1. **Interface/API** : parse les requêtes, applique le contrat HTTP et transforme les résultats en réponses.
2. **Services applicatifs** : orchestrent préparation, tokenisation, entraînement, sélection de run et génération.
3. **Composants de domaine** : règles de validation, états de job, configuration de run, provenance des corpus.
4. **Adaptateurs** : filesystem, PyTorch, Hugging Face, calcul CPU/GPU et éventuelle file de jobs.
5. **Application web** : reste cliente des contrats publics ; tout changement de contrat est coordonné.

Le PRD devra décider si l'exécution reste dans un seul processus ou passe à un worker durable, si les fichiers restent le stockage de référence, et si l'API garde Flask.

## Stratégie de migration proposée

- **Étape A — Caractériser** : figer contrats, exemples d'artefacts et décisions RC_1/RC_3.
- **Étape B — Encapsuler** : extraire les cas d'usage derrière des interfaces testables en conservant les routes existantes.
- **Étape C — Fiabiliser les données et jobs** : unifier chemins, schémas de configuration, états, progression et gestion d'erreur.
- **Étape D — Aligner représentation et modèle** : migrer après choix explicite BPE/byte-level ; préserver une lecture explicite des anciens artefacts.
- **Étape E — Remplacer progressivement** : basculer route par route avec tests de non-régression et possibilité de retour arrière.
- **Étape F — Retirer l'ancien chemin** : seulement après validation des usages CLI/dashboard et des artefacts historiques.

Cet ordre est une proposition ; valider les dépendances avant de l'utiliser comme plan d'exécution.

## Exigences de qualité non fonctionnelles

- Composants isolables et testables sans GPU, réseau ni données privées.
- Configuration centralisée, validée et sans mutation implicite de valeurs globales.
- Erreurs observables avec contexte utile mais sans divulguer prompts, corpus ou données personnelles par défaut.
- Écritures d'artefacts résilientes aux interruptions et à la concurrence.
- Chargement paresseux des dépendances coûteuses lorsque possible.
- Limites CPU/mémoire/concurrence et exigences de délai mesurables pour chaque opération.
- Déploiement local documenté, avec dépendances minimales et commandes de vérification.

## Critères d'acceptation

- Les responsabilités et dépendances sont représentées sans cycle entre API, domaine et stockage.
- Chaque étape de migration possède critères d'entrée/sortie, plan de retour arrière et artefacts concernés.
- Les interfaces CLI et dashboard préservées sont listées et testées.
- Le plan ne supprime pas ni ne réécrit les checkpoints et corpus historiques sans migration documentée.
