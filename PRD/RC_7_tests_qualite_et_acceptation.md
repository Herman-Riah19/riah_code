# RC_7 — Stratégie de tests, qualité et critères de livraison

## Mission

Définir la preuve de conformité requise pour chaque étape de réécriture et pour la livraison complète. Les seuils de performance doivent être mesurés sur l'environnement cible puis validés, et non inventés.

## Niveaux de test à inclure dans le PRD

### Tests unitaires

- Nettoyage VTT : métadonnées, timestamps, tags, doublons consécutifs et texte Unicode.
- Normalisation LinkedIn/Instagram : champs manquants, ordre chronologique, extraction récursive et locuteurs.
- Nettoyage Wikipédia : blocs LaTeX, ligne conservée/supprimée et sortie vide.
- Filtrage streaming : texte court, détection FR, quotas documents/octets et compteurs.
- Tokenizer : déterminisme de la configuration, sauvegarde/rechargement et encode/decode.
- Modèle : masque causal, dimensions, décalage next-token, padding, perte et génération bornée.
- Jobs : transitions d'état, progression, refus d'un deuxième job incompatible, arrêt et échec.

### Tests d'intégration

- Préparer un mini-corpus local et vérifier le manifeste, le catalogue et les compteurs.
- Entraîner un modèle minuscule sans GPU, sauvegarder puis reprendre un checkpoint compatible.
- Tester chaque contrat HTTP avec requête valide, absente, mal formée et conflit d'état.
- Tester que les champs utilisés par le dashboard restent cohérents avec l'API.
- Vérifier qu'un redémarrage ou une interruption suit la politique de jobs et d'artefacts retenue.

### Qualité et exploitation

- Exécuter le formateur/linter, l'analyse de types disponible et la suite de tests du dépôt.
- Vérifier l'installation depuis les dépendances documentées sur une machine CPU sans données externes.
- Mesurer temps, mémoire et taille d'artefacts sur corpus représentatif et sur les cas limites retenus.
- Contrôler que les logs et erreurs n'exposent pas de texte privé ou de chemins sensibles.
- Vérifier le traitement des checkpoints anciens et l'absence de corruption après arrêt contrôlé.

## Exigences de livraison

- Les tests déterminants sont automatisés et reproductibles sur fixtures synthétiques.
- Tout accès réseau est isolé derrière un adaptateur ; aucun test standard ne dépend d'un dataset distant.
- Les tests GPU sont optionnels et ne bloquent pas le parcours CPU de base.
- Les seuils de génération, durée, mémoire, taille de données et précision des métriques sont fixés avec une méthode de mesure.
- Chaque critère d'acceptation fonctionnel des RC_1 à RC_6 est relié à au moins un test ou une vérification d'exploitation.
- Les limites connues, choix incompatibles et procédure de retour arrière sont documentés.

## Conditions de sortie

La réécriture peut être considérée prête lorsque les contrats sont validés, les critères fonctionnels passent, la stratégie d'artefacts/checkpoints est vérifiée et le dashboard/CLI utilisent les interfaces prévues. Toute fonctionnalité volontairement retirée doit être listée et approuvée avant la bascule.
