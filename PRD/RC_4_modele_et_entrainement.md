# RC_4 — Spécification du modèle et de l'entraînement

## Mission

Décrire l'algorithme d'entraînement actuel et les exigences pour le réimplémenter proprement, avec des configurations validées, des runs reproductibles et une reprise fiable.

## Algorithmes observés

Dans [`scripts/train_subtitles_transformer.py`](../scripts/train_subtitles_transformer.py) :

- Le corpus rassemble les fichiers texte des répertoires sélectionnés, les encode en UTF-8 et les concatène avec le séparateur `\n\n<|doc|>\n\n`. Le modèle actuel consomme ensuite les octets, pas les unités BPE.
- La séquence est séparée en blocs d'entraînement et de validation selon `train_split`. `ByteDataset` prend des fenêtres contiguës de `block_size + 1`, crée la cible par décalage d'un token et tire aléatoirement une longueur entre `min_seq_len` et la longueur disponible. Le collateur complète les séquences et fournit masque de padding.
- Le réseau combine embedding de tokens, encodage positionnel sinusoïdal, `TransformerEncoder` PyTorch avec masque causal triangulaire supérieur, GELU, dropout, LayerNorm et tête linéaire vers le vocabulaire. Le poids de la tête est partagé avec l'embedding lorsque les dimensions concordent.
- L'objectif est l'entropie croisée des logits sur les tokens suivants. L'optimiseur est AdamW ; les gradients sont écrêtés à une norme maximale de 1.0.
- Le générateur applique température, filtrage top-k optionnel puis échantillonnage multinomial.
- Des presets définissent taille d'architecture, batch, longueur, cadence d'évaluation et d'échantillonnage. La graine Python/PyTorch/CUDA par défaut est 13.
- L'évaluation moyenne l'entropie croisée sur un nombre plafonné de batches. Les métriques, exemples, visualisations PCA des embeddings et logits, métadonnées et checkpoints sont écrits dans le répertoire du run.
- La reprise recharge les poids du modèle et, si disponible, l'état AdamW. Le run en cours reçoit un statut et des journaux de progression ; un événement d'arrêt est vérifié entre les étapes.

## Exigences à formaliser

- Définir les paramètres valides et leurs relations : dimensions divisibles par le nombre de têtes, limites de contexte, vocabulaire, taux, batch, fraction train/validation et intervalles.
- Définir précisément la séparation des données (par document recommandé à évaluer, au lieu de couper arbitrairement un flux concaténé) et prévenir toute fuite train/validation.
- Choisir la métrique d'évaluation, la population échantillonnée et la politique de padding afin que le score ne dépende pas d'éléments de padding.
- Exiger la persistance cohérente des états : modèle, optimiseur, étape, graine, tokenizer/représentation et configuration complète.
- Définir les états de run : en attente, en cours, terminé, arrêté, échoué ; rendre la progression et les erreurs lisibles.
- Définir ce qui est produit à chaque étape et la politique de rétention des checkpoints, métriques, exemples et visualisations.
- Définir les garanties de reproductibilité réalistes selon CPU/GPU et la gestion du manque de mémoire.
- Décider si l'échantillonnage et les visualisations sont activables indépendamment, et établir leurs coûts/limites.
- Fixer le comportement d'une reprise avec configuration ou forme de modèle différente : refuser proprement ou offrir une migration explicite.

## Critères d'acceptation

- Une expérience est reconstructible à partir de sa configuration et de ses artefacts.
- La reprise produit un état cohérent et refuse les checkpoints incompatibles avec une explication exploitable.
- Des tests valident le décalage source/cible, le masque causal, le padding, l'arrêt et l'enregistrement des métriques.
- Les configurations invalides sont rejetées avant de démarrer un thread ou de créer des fichiers de run.
