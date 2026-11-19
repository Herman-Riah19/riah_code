# AGENTS.md — Règles Frontend pour l'application Web

Ce fichier guide les agents intervenant dans le répertoire `web/`.
Consulter également [CODING_RULES.md](file:///d:/Project/riah_code/web/CODING_RULES.md).

## Règles Impératives

1. **ZÉRO BALISE HTML PRIMITIVE DANS LES PAGES ET COMPOSANTS** :
   - Jamais de `<div>`, `<span>`, `<p>`, `<button>`, `<input>`, `<ul>`, `<li>`, etc. directement dans vos vues ou pages.
   - Composez systématiquement à l'aide des composants Atomes du Design System :
     `<Box>`, `<Flex>`, `<Stack>`, `<Text>`, `<Heading>`, `<Button>`, etc.
2. **COMPOSANTS GÉNÉRIQUES ET RÉUTILISABLES** :
   - Aucun composant ne doit être personnalisé pour une seule page ou un seul cas d'usage.
   - Utiliser des props de variantes (`variant`, `size`, `colorScheme`, etc.) et la composition (`children`, slots).
3. **STORYBOOK (CDD)** :
   - Chaque Atome, Molécule ou Organisme doit avoir son fichier `*.stories.tsx` documenté.
4. **ARCHITECTURE ATOMIC DESIGN** :
   - `atoms/` → `molecules/` → `organisms/` → `templates/` → `pages/`.
