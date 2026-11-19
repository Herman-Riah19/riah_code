# RC_3 — Spécification du corpus et du tokenizer

## Mission

Définir la représentation des données consommée par l'entraînement et l'inférence, puis résoudre l'écart entre le tokenizer BPE entraîné et le modèle byte-level actuel.

## Comportement existant

Dans [`scripts/train_tokenizer.py`](../scripts/train_tokenizer.py), les fichiers `.txt` sont parcourus récursivement et triés. Une limite optionnelle de fichiers et une limite optionnelle d'octets sélectionnent les fichiers à entraîner. Le tokenizer est un BPE Hugging Face avec normalisation NFD, suppression des accents, casse optionnelle, pré-tokenizer ByteLevel, alphabet initial ByteLevel et tokens spéciaux `[PAD]`, `[UNK]`, `[CLS]`, `[SEP]`, `[MASK]`. Un post-processeur ajoute CLS et SEP aux séquences.

Le résultat est enregistré avec `tokenizer.json` et `metadata.json`. L'API permet de tester un tokenizer sélectionné et renvoie tokens, IDs, attention mask, longueur et rendu lisible des segments.

En revanche, [`scripts/train_subtitles_transformer.py`](../scripts/train_subtitles_transformer.py) lit le texte en octets UTF-8 et utilise les valeurs d'octets (0 à 255) comme identifiants. Le tokenizer BPE n'est pas chargé pendant le training ni le chat. Les presets utilisent néanmoins un vocabulaire de taille supérieure aux 256 identifiants d'octets. Cette divergence est une décision bloquante, pas un détail d'implémentation.

## Décisions requises

Choisir et documenter une seule stratégie de bout en bout :

1. **Byte-level** : définir l'alphabet, les valeurs réservées et la taille exacte du vocabulaire ; retirer ou repositionner le BPE si le produit n'en a pas l'usage.
2. **BPE** : définir comment tokenizer et modèle sont versionnés ensemble, comment le corpus est encodé et comment le même tokenizer est chargé en génération.

Le PRD doit comparer les options selon qualité linguistique, coût mémoire/calcul, compatibilité checkpoints, simplicité d'exploitation et facilité de migration. Ne pas convertir silencieusement les anciens checkpoints.

## Exigences à formaliser

- Une configuration d'entraînement/inférence référence de manière immuable la représentation et, si applicable, la version/hash du tokenizer.
- La taille du vocabulaire et les identifiants spéciaux correspondent réellement aux données données au modèle.
- Les paramètres Unicode (accents, casse, ByteLevel, tokens spéciaux, offsets) ont un contrat vérifié entre entraînement, API et widget de test.
- Les limites de corpus sont exprimées sans ambiguïté (fichiers, octets lus ou taille après normalisation).
- Les manifestes identifient les sources et configurations de corpus contribuant au tokenizer et au modèle.
- Les anciennes métadonnées et checkpoints sont détectés et signalés comme compatibles, migrables ou non pris en charge.
- Les textes vides, encodages invalides, corpus trop petits et paramètres hors limites donnent des erreurs compréhensibles.

## Critères d'acceptation

- Une même chaîne encode et se décode conformément aux règles retenues dans le training et en inférence.
- Les identifiants générés sont dans la plage d'embedding déclarée et les tokens spéciaux ne sont pas confondus avec du texte brut.
- Un artefact de modèle pointe vers la représentation exacte avec laquelle il a été entraîné.
- Une décision de compatibilité est documentée pour les checkpoints byte-level existants.
