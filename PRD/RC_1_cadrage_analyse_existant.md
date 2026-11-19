# RC_1 — Cadrage et analyse de l'existant

## Mission

Établir le périmètre fonctionnel du remplacement de l'API Flask et de ses traitements associés, en conservant les usages réellement nécessaires au tableau de bord. Ce document est un point de départ pour rédiger le PRD détaillé, pas une décision de réarchitecture déjà figée.

## Périmètre observé

Le point d'entrée étudié est [`dashboard/server.py`](../dashboard/server.py). Il importe les préparateurs et le modèle décrits dans les fiches suivantes : pipeline de données (RC_2), tokenizer (RC_3), entraînement (RC_4), API et inférence (RC_5).

Le système assure actuellement :

1. la préparation de corpus depuis des fichiers locaux et des jeux de données Hugging Face ;
2. l'entraînement d'un tokenizer BPE ;
3. l'entraînement et la reprise d'un modèle de langage Transformer ;
4. la persistance des runs, métriques, checkpoints, échantillons et historiques en fichiers ;
5. la consultation et le contrôle de ces travaux via une API JSON Flask ;
6. la génération de texte et le test d'un tokenizer.

## Acteurs et besoins

- **Opérateur / utilisateur du dashboard** : lancer et suivre les traitements, choisir un run, entraîner/reprendre/arrêter un modèle, tester un tokenizer et générer du texte.
- **Développeur** : pouvoir modifier les briques séparément, vérifier leur comportement et éviter qu'une modification de l'API ne casse les scripts, les artefacts ou le dashboard.
- **Propriétaire des données** : contrôler les répertoires lus/écrits et la manipulation des exports personnels LinkedIn/Instagram.

## Parcours fonctionnel à préserver

- L'API expose métadonnées, runs, métriques et visualisations.
- Les tâches de préparation, le tokenizer et l'entraînement s'exécutent en arrière-plan et exposent leur état.
- Un run peut être sélectionné ; un entraînement peut être lancé, repris depuis un checkpoint ou arrêté.
- Le chat utilise un checkpoint chargé et renvoie le texte généré.
- Le test tokenizer renvoie tokens, identifiants, masque, longueur et segments lisibles.
- Les scripts CLI de préparation et d'entraînement doivent rester utilisables, sauf décision explicite de les retirer.

## Constats importants vérifiés

- Le serveur est un module monolithique : état global à la fabrique d'application, routes, tâches, sérialisation des données et chargement du modèle cohabitent.
- Les tâches sont des threads daemon en mémoire. Leur état ne survit pas à un redémarrage du serveur.
- Les artefacts sont des fichiers JSON/JSONL/TXT et des checkpoints PyTorch dans les répertoires du dépôt.
- Le code utilise des écritures directes, des valeurs par défaut et des validations de requête hétérogènes.
- **Désaccord tokenizer/modèle à clarifier** : `train_tokenizer.py` entraîne un vocabulaire BPE (par défaut 32 000 entrées), tandis que l'entraînement du modèle convertit le corpus en octets UTF-8 et utilise des identifiants d'octets. Le tokenizer entraîné n'est pas utilisé par le modèle actuel.
- **Chemins de sous-titres à clarifier** : l'API convertit par défaut vers `youtube-subtitile-plain`, alors que le catalogue de données inspecte `data_clean/youtube`. Le script complet a aussi une étape de copie/mise en miroir ; le déclenchement dashboard n'utilise pas ce parcours complet.
- Les importations sociales construisent des transcriptions avec des étiquettes `Assistant` / `User`. La nature personnelle de ces données doit être prise en compte dans les exigences de conservation, d'accès et de suppression.

## Décisions produit/techniques à prendre avant de figer le PRD

1. Le tokenizer BPE doit-il devenir le tokenizer d'entraînement/inférence, ou le modèle doit-il rester byte-level ? Le vocabulaire, les checkpoints et la compatibilité dépendent de ce choix.
2. Quelle est la source de vérité pour le corpus de sous-titres et où le dashboard doit-il écrire ?
3. Le dashboard doit-il exposer toutes les préparations disponibles en CLI, et lesquelles nécessitent un accès réseau ?
4. Les runs et historiques doivent-ils rester sur le système de fichiers ? Faut-il reprendre un job après redémarrage ?
5. Quels sont les formats d'artefacts et les engagements de compatibilité à conserver pour les anciens checkpoints ?
6. Quelle politique s'applique aux exports personnels et aux logs contenant des chemins ou du texte de corpus ?
7. Quels objectifs de déploiement (local uniquement, multi-utilisateur, GPU optionnel) sont requis ?

## Consigne de rédaction du PRD

À partir des réponses ci-dessus, rédiger des exigences fonctionnelles et non fonctionnelles traçables. Séparer explicitement les comportements observés, les comportements souhaités et les choix restant ouverts. Ne pas traiter les valeurs par défaut du code actuel comme des exigences produit sans validation.

## Critères d'acceptation

- Les parcours utilisateurs à préserver et les limites de périmètre sont validés.
- Chaque décision ouverte a un propriétaire ou une réponse.
- Les choix tokenizer/vocabulaire et répertoire de données sont résolus avant de définir la migration des checkpoints.
- Les exigences du PRD peuvent être reliées aux étapes RC_2 à RC_7.
