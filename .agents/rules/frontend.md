# Règle Antigravity : Frontend React, Atomic Design & Storybook

Cette règle s'applique à tous les fichiers du sous-dossier `web/` (`*.tsx`, `*.ts`, `*.css`).

## 1. Zéro Balise Primitive dans les Composants Métier & Pages

- **INTERDIT** : Écrire directement `<div>`, `<section>`, `<span>`, `<p>`, `<h1>`-`<h6>`, `<button>`, `<input>`, `<ul>`, `<li>`, `<a>`, etc. dans les pages, templates, organismes ou molécules.
- **OBLIGATOIRE** : Utiliser exclusivement les composants Atomes du Design System (`Box`, `Flex`, `Stack`, `Text`, `Heading`, `Button`, etc.).
- Si un élément HTML manquant est requis, créer d'abord un Atome générique dans `src/components/atoms/`.

## 2. Atomic Design Strict

- `atoms/` : Briques UI élémentaires et indivisibles. Seuls autorisés à rendre des éléments HTML réels.
- `molecules/` : Combinaisons simples d'atomes sans logique métier de page.
- `organisms/` : Blocs complexes réutilisables d'interface.
- `templates/` : Structures de mise en page pures (slots, wireframes).
- `pages/` : Instanciations de templates injectant les données via hooks/services.

## 3. Composants Génériques & Réutilisables

- Ne JAMAIS créer de composants personnalisés pour une seule page (ex: pas de `DashboardHeader`, mais un `PageHeader` configurable par props).
- Paramétrer le comportement et le rendu via des props typées : `variant`, `size`, `colorScheme`, `isLoading`, `isDisabled`.
- Favoriser la composition (`children`, slots) sur la rigidité.

## 4. Intégration Storybook Obligatoire (CDD)

- Chaque Atome, Molécule et Organisme doit posséder son fichier `*.stories.tsx` dans son sous-dossier dédié.
- Documenter les arguments (`argTypes`) et présenter les variantes principales et les états spéciaux (Loading, Disabled, Error).

## 5. Qualité React 19 & TypeScript

- TypeScript strict sur toutes les interfaces de props. Pas de `any`.
- Accessibilité (ARIA, navigation clavier, rôles sémantiques).
- Dérivation d'état plutôt que synchronisation par `useEffect`.
