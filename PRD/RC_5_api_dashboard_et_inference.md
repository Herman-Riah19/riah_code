# RC_5 — Spécification API, dashboard et inférence

## Mission

Figer les contrats externes de l'API observée dans [`dashboard/server.py`](../dashboard/server.py) avant de séparer routes, services et exécution des jobs.

## Routes actuelles

| Méthode et route | Fonction observée |
|---|---|
| `GET /metadata` | Configuration par défaut, run sélectionné, checkpoints/modèle, jobs, catalogue, historique, presets et tokenizers. |
| `GET /metrics` | Métriques train/validation du run sélectionné depuis JSONL. |
| `GET /visuals` | Jusqu'aux 60 dernières visualisations du run sélectionné. |
| `GET /runs` | Runs détectés dans le système de fichiers, triés du plus récent au plus ancien. |
| `POST /select` | Sélectionne un répertoire de run et tente de charger son checkpoint. |
| `POST /chat` | Génère du texte à partir d'un prompt et d'options de sampling. |
| `POST /data/prepare`, `GET /data/status` | Démarre et suit une tâche de préparation. |
| `POST /train`, `GET /train/status`, `POST /train/resume`, `POST /train/stop` | Démarre, suit, reprend et arrête l'entraînement. |
| `POST /tokenizer/train`, `GET /tokenizer/status`, `POST /tokenizer/test` | Entraîne, suit et teste un tokenizer. |

Les réponses sont JSON ; les erreurs de requête utilisent plusieurs codes HTTP (notamment 400, 404, 409, 500 et 503). Les détails exacts de tous les champs doivent être extraits et versionnés dans le PRD API.

## Algorithme d'inférence actuel

`ModelRunner` charge un checkpoint sur CPU, reconstruit la configuration, instancie le Transformer, restaure les poids puis passe en mode évaluation. Pour générer, le serveur encode le contexte et le prompt en octets UTF-8, borne la fenêtre au `block_size`, calcule les logits du dernier élément, divise par la température, masque les logits hors top-k si demandé et échantillonne une valeur avec multinomial. Les octets échantillonnés sont convertis en texte UTF-8 avec caractères invalides ignorés.

La route chat préfixe le message par `Utilisateur:` et `Assistant:` puis applique un saut de ligne au contexte. Elle vérifie que le message utilisateur n'est pas vide. Les autres paramètres reçoivent des conversions de types qui peuvent échouer avant la réponse JSON dédiée ; les limites de génération et le top-k doivent être spécifiés dans le contrat cible.

## Exigences à formaliser

- Définir les schémas de requête/réponse, champs obligatoires, valeurs par défaut, limites, codes d'erreur et versionnement pour chaque route.
- Valider les paramètres avant exécution (dont température, top-k, nombre de tokens, chemins et types) et retourner des erreurs stables et localisables.
- Définir le modèle de concurrence : plusieurs jobs simultanés autorisés ou non, capacité de chat pendant l'entraînement, visibilité des jobs entre processus et comportement au redémarrage.
- Définir une politique d'état atomique, de chargement/sélection des checkpoints et de réponse si un chargement échoue.
- Fixer les limites de taille des entrées/sorties, délais d'attente et comportement d'arrêt client.
- Définir une autorisation d'accès aux fichiers cohérente pour sélectionner/reprendre un run ; ne jamais dépendre d'un chemin fourni par la requête sans validation métier.
- Garantir que la sortie du générateur respecte le format et les limites de texte définis, sans perte silencieuse de caractères non décodables.
- Préserver les champs utilisés par le dashboard, ou planifier leur migration de manière coordonnée avec celui-ci.

## Critères d'acceptation

- Les contrats de toutes les routes sont documentés et couverts par tests HTTP.
- Les erreurs sont JSON, explicites et cohérentes ; les entrées mal formées n'entraînent ni exception non gérée ni job partiellement démarré.
- Les scénarios concurrent, arrêt, sélection et chargement impossible ont des résultats définis.
- Un test d'intégration parcourt l'état de run, la lecture des métriques et une génération bornée avec un checkpoint de test.
