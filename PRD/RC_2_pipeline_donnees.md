# RC_2 — Spécification du pipeline de données

## Mission

Décrire le contrat fonctionnel des sources, transformations et artefacts de corpus. Utiliser les scripts présents comme référence de comportement, en distinguant les algorithmes existants des améliorations à décider.

## Sources et algorithmes observés

### Sous-titres VTT

Dans [`scripts/clean_vtt.py`](../scripts/clean_vtt.py), chaque ligne est écartée si elle est vide, ressemble à un en-tête ou à une métadonnée VTT, contient un timestamp, commence par un attribut de positionnement, ne contient qu'un nombre ou correspond à une didascalie entre crochets. Le script enlève ensuite les balises, les espaces zéro largeur, normalise les espaces et retire les répétitions consécutives identiques. Les lignes conservées sont écrites dans un fichier texte.

Le parcours complet synchronise les fichiers des chaînes, convertit les VTT, puis copie les textes vers `data_clean/youtube`. Le job du serveur convertit seulement les fichiers du répertoire source vers la cible demandée/par défaut. Spécifier un unique parcours canonique et rendre les reprises idempotentes.

### LinkedIn

Dans [`scripts/prepare_linkedin.py`](../scripts/prepare_linkedin.py), les CSV sont lus en UTF-8 avec BOM toléré. Les retours à la ligne, guillemets et espaces multiples sont normalisés. Commentaires et partages sont exportés en lignes. Les messages sont regroupés par identifiant de conversation, triés chronologiquement, puis étiquetés selon le nom configuré comme `Assistant` ou `User`.

### Instagram

Dans [`scripts/prepare_instagram.py`](../scripts/prepare_instagram.py), les JSON de messages de chaque fil sont fusionnés et triés par timestamp milliseconde ; les locuteurs sont classés selon une liste de noms propres, les autres devenant `User`. Les commentaires sont extraits récursivement des clés de commentaires connues. Une correction heuristique d'encodage mojibake est tentée avant l'export.

### Wikipédia déjà téléchargée

Dans [`scripts/clean_wikipedia.py`](../scripts/clean_wikipedia.py), des expressions régulières éliminent des blocs mathématiques/LaTeX, remplacent certaines commandes en ligne, suppriment commandes, accolades et références numériques. Les lignes sont compactées ; celles qui restent vides ou ont une forte densité de symboles sont supprimées. Les sorties sont écrites via fichier temporaire puis renommage.

### FineWeb et OSCAR

- [`scripts/download_fineweb.py`](../scripts/download_fineweb.py) parcourt un dataset Hugging Face en streaming, normalise les retours à la ligne, impose une longueur minimale et utilise `langdetect` sur un préfixe borné. La graine du détecteur est fixée à 13 et le document n'est gardé que si la probabilité `fr` atteint le seuil. Un plafond de documents conservés et un plafond d'octets peuvent interrompre le flux.
- [`scripts/download_oscar.py`](../scripts/download_oscar.py) parcourt en streaming le dataset, extrait le premier champ de texte disponible, normalise les retours de ligne et applique une longueur minimale. Le dataset étant déjà filtré par langue, aucun détecteur supplémentaire n'est appliqué.
- Les deux scripts concatènent les documents avec un séparateur `<|doc|>` et écrivent un fichier de métadonnées JSON avec compteurs et configuration.

## Exigences à formaliser

- Définir un contrat par source : formats d'entrée, encodage, champs obligatoires/optionnels, règles de nettoyage, format de sortie, erreurs et compteurs.
- Rendre les règles déterministes et configurables là où cela a une valeur produit (ex. noms de locuteurs, seuil de langue, longueur minimale, quotas).
- Préserver la provenance par source et par document, sans mélanger silencieusement les corpus.
- Définir la politique concernant doublons, fichiers invalides, documents vides, caractères mal encodés et erreurs réseau.
- Rendre explicites les limites : nombre de documents, taille, durée, progression et annulation.
- Garantir que l'utilisateur peut distinguer « terminé sans document », « terminé avec données », « échoué » et « annulé ».
- Définir une stratégie de sortie sûre : écriture temporaire/atomique, comportement en cas de relance et protection contre l'écrasement d'un corpus non visé.
- Définir explicitement les répertoires canoniques, incluant la divergence observée pour les sous-titres.
- Pour LinkedIn/Instagram, prévoir des règles de confidentialité, rétention, effacement et journalisation minimisée.

## Flux cible à préciser

`source brute → validation/lecture → normalisation → filtres spécifiques à la source → sortie isolée + manifeste → catalogage → sélection du corpus d'entraînement`.

Cette séquence est une proposition de découpage logique, pas une prescription d'implémentation. Le PRD doit décider si des étapes intermédiaires sont persistées et si une provenance détaillée est nécessaire.

## Critères d'acceptation

- Chaque source utilisée a une fiche de contrat et des exemples d'entrée/sortie représentatifs.
- Les règles exactes de sélection et les compteurs de rejet sont définis.
- Les limites et le comportement de reprise/annulation sont testables.
- L'emplacement des sous-titres et l'inclusion des sources dans le corpus sont univoques.
- Les données personnelles ne sont pas ajoutées aux journaux ou sorties hors des choix explicitement approuvés.
