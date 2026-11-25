# CODING RULES — Frontend React, Atomic Design & Storybook

Ce document définit les règles impératives, l'architecture et les standards de développement pour l'application frontend (`web/`).

---

## 1. Règle Fondamentale : Interdiction des Balises HTML Primitives

> [!CAUTION]
> **INTERDICTION FORMELLE D'UTILISER DES BALISES HTML PRIMITIVES DANS LES PAGES, VUES, ORGANISMES ET MOLÉCULES.**
> Il est strictement interdit d'écrire directement :
> `<div>`, `<section>`, `<article>`, `<header>`, `<footer>`, `<main>`, `<aside>`, `<span>`, `<p>`, `<h1>`–`<h6>`, `<button>`, `<input>`, `<textarea>`, `<select>`, `<form>`, `<ul>`, `<ol>`, `<li>`, `<a>`, `<table>`, etc.

### Pourquoi cette règle ?
1. **Cohérence visuelle et Design System centralisé** : Toute modification de style, de thème, d'espacement ou d'accessibilité se fait dans les composants de base (Atomes), sans régression dans le reste de l'application.
2. **Accessibilité (a11y) native** : Les composants Atomes gèrent correctement les attributs ARIA, les rôles, les états de focus et la navigation clavier.
3. **Typage et maintenabilité** : Évite le code spaghetti et le CSS dispersé dans des balises primitives non typées.

### Comment construire une interface ?
Toute interface doit être composée **exclusivement** en assemblant des composants du Design System :

```tsx
// ❌ FORMELLEMENT INTERDIT
export const UserCard = () => {
  return (
    <div className="card">
      <div className="card-header">
        <h1>Profil</h1>
        <p>Description de l'utilisateur</p>
      </div>
      <button onClick={() => alert('ok')}>Valider</button>
    </div>
  )
}

// ✅ OBLIGATOIRE : Composition d'Atomes / Molécules existants
import { Box } from '@/components/atoms/Box'
import { Heading } from '@/components/atoms/Heading'
import { Text } from '@/components/atoms/Text'
import { Button } from '@/components/atoms/Button'
import { Stack } from '@/components/atoms/Stack'

export const UserCard = () => {
  return (
    <Box padding="md" borderRadius="lg" border="subtle">
      <Stack direction="vertical" spacing="sm">
        <Heading level={1} size="xl">Profil</Heading>
        <Text color="muted" size="sm">Description de l'utilisateur</Text>
        <Button variant="primary" onClick={() => alert('ok')}>
          Valider
        </Button>
      </Stack>
    </Box>
  )
}
```

> [!NOTE]
> **Si un besoin HTML primitif n'est pas encore couvert par un Atome**, la règle est de **créer un nouvel Atome générique** (ex: `Radio`, `Checkbox`, `Table`, `Badge`) dans `src/components/atoms/`, accompagné de ses types, de son histoire Storybook et de ses variantes, **avant** de l'utiliser.

---

## 2. Architecture : Atomic Design

L'arborescence des composants respecte la hiérarchie stricte d'Atomic Design :

```
web/src/
├── components/
│   ├── atoms/          # Briques élémentaires et indivisibles (Box, Text, Button, Input...)
│   ├── molecules/      # Combinaisons simples d'atomes (FormField, SearchBar, StatCard...)
│   ├── organisms/      # Sections d'interface autonomes (Navbar, Sidebar, MetricsTable...)
│   └── templates/      # Structures de mise en page sans données métier (DashboardLayout...)
├── pages/              # Vues réelles associant les templates, hooks et état métier
├── hooks/              # Custom React hooks (logique réutilisable)
├── services/           # Appels API et clients HTTP
├── types/              # Types TypeScript partagés
└── utils/              # Fonctions utilitaires pures
```

### 2.1. Les Atomes (`src/components/atoms/`)
- Les composants les plus basiques, indivisibles.
- Ne contiennent **aucune logique métier ni appel API**.
- Sont les **seuls** composants autorisés à rendre des éléments HTML sous-jacents (`div`, `span`, `button`...).
- Supportent des props polymorphiques (`as?: 'div' | 'section' | 'article'`) ou des variantes d'affichage claires (`variant`, `size`, `colorScheme`).
- **Exemples** : `Box`, `Flex`, `Grid`, `Stack`, `Text`, `Heading`, `Button`, `Input`, `Badge`, `Icon`, `Spinner`.

### 2.2. Les Molécules (`src/components/molecules/`)
- Assemblage de 2 ou plusieurs Atomes fonctionnant comme une unité fonctionnelle simple.
- Ne contiennent pas de logique métier liée à une page spécifique ; elles restent 100% réutilisables.
- **Exemples** :
  - `FormField` = `Label` (Text) + `Input` + `ErrorMessage` (Text)
  - `SearchBar` = `Input` + `IconButton` (Button + Icon)
  - `StatCard` = `Box` + `Icon` + `Heading` + `Text`
  - `Textfield` = `Label` (Text) + controle (Input / Select / Textarea) + aide ou erreur
  - `StatTile` = libelle + valeur en gras/mono + indication optionnelle
  - `ButtonGroup` = ensemble de `Button`

### 2.3. Les Organismes (`src/components/organisms/`)
- Combinaison de molécules et d'atomes formant des blocs d'interface complets et cohérents.
- Peuvent gérer des interactions locales (état d'ouverture d'un menu, onglet actif).
- Doivent rester réutilisables et découplés d'une page unique (recevoir les données ou handlers par props).
- **Exemples** : `AppHeader`, `SidebarNavigation`, `DataTable`, `ChatBubbleGroup`, `MetricsDashboardGrid`.

### 2.4. Les Templates (`src/components/templates/`)
- Gabarits de structure de page (wireframes).
- Définissent les zones d'affichage (ex: header slot, sidebar slot, content slot).
- Ne contiennent pas de données en dur.
- **Exemples** : `DashboardTemplate`, `AuthTemplate`, `SettingsTemplate`.

### 2.5. Les Pages (`src/pages/`)
- Instancient un Template et y injectent les Organismes avec les données réelles (via hooks, stores ou API).

---

## 3. Règle de Conception : Composants Génériques vs Dédiés à une Page

> [!IMPORTANT]
> **Interdiction formelle de créer des composants "personnalisés pour une seule page".**

1. **Pas de composants nommés d'après une page** :
   - ❌ Interdit : `DashboardHeader`, `TrainPageCustomButton`, `ChatModelDropdownSpecific`
   - ✅ Correct : `PageHeader`, `Button`, `Select`
2. **Paramétrage par props et variantes** :
   - Un composant doit être conçu pour fonctionner dans n'importe quel contexte de l'application.
   - Les variations de style se gèrent via des props typées : `variant`, `size`, `intent`, `isFullWidth`, `isDisabled`, `isLoading`.
3. **Inversion de contrôle (Slots / `children`)** :
   - Favoriser la composition plutôt que la multiplication de props rigides.
   - Préférer `leftIcon?: ReactNode` ou `children` plutôt qu'un texte rigide imposé.

### 3.4. Factorisation des patterns repetitifs en molecules

Quand un même assemblage d'atomes (libelle + controle, tuile libelle/valeur, carte
panneau, etc.) apparait **au moins deux fois** dans l'application, il doit etre
extrait dans une molecule dediee sous `src/components/molecules/` :

- **Pattern label + controle** (`<Stack><Text label /><Input /></Stack>`) → `Textfield`
- **Pattern libelle + valeur en mono** → `StatTile`
- Tout composant extrait doit posseder son fichier `*.stories.tsx` (Storybook).

Interdit de dupliquer ce type de assemblage "en ligne" dans plusieurs composants.

---

## 4. Bonnes Pratiques React 19 & TypeScript

### 4.1. TypeScript Strict & Déclaration de Props
- Chaque composant a une interface ou type explicite pour ses props :
  ```tsx
  export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
    size?: 'sm' | 'md' | 'lg'
    isLoading?: boolean
    leftIcon?: React.ReactNode
    rightIcon?: React.ReactNode
  }
  ```
- Pas de `any`. Toujours typer les événements (`React.MouseEvent`, `React.ChangeEvent`).
- Définir des valeurs par défaut claires pour les props optionnelles.

### 4.2. Accessibilité (a11y)
- Tout composant interactif (`Button`, `Input`, `Dialog`) doit être accessible au clavier (`Tab`, `Enter`, `Escape`).
- Gestion adéquate des attributs `aria-label`, `aria-expanded`, `aria-busy`, `aria-invalid`.
- Contrastes de couleurs conformes aux standards WCAG.

### 4.3. Gestion d'État et Hooks
- Éviter les états redondants : toujours dériver l'état calculé (`const fullName = firstName + ' ' + lastName`) plutôt que de stocker un état synchronisé dans `useEffect`.
- Isoler la logique complexe dans des Custom Hooks (`useTrainingJob`, `useInferenceChat`).

---

## 5. Intégration Storybook & Component-Driven Development (CDD)

Chaque composant créé dans `atoms/`, `molecules/` ou `organisms/` **doit** impérativement être accompagné de sa Story Storybook (`*.stories.tsx`).

### 5.1. Structure d'un dossier composant
Chaque composant possède son propre répertoire dédié :
```
src/components/atoms/Button/
├── Button.tsx           # Implémentation React
├── Button.types.ts      # Définition des types et interfaces
├── Button.module.css    # Styles modulaires ou classes utilitaires
├── Button.stories.tsx   # Déclaration des histoires Storybook
└── index.ts             # Point d'export propre
```

### 5.2. Standard d'écriture d'une Story
```tsx
import type { Meta, StoryObj } from '@storybook/react'
import { Button } from './Button'

const meta: Meta<typeof Button> = {
  title: 'Atoms/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'outline', 'ghost', 'danger'],
      description: 'Variante visuelle du bouton',
    },
    size: {
      control: 'radio',
      options: ['sm', 'md', 'lg'],
      description: 'Taille du bouton',
    },
    isLoading: {
      control: 'boolean',
      description: 'Affiche un indicateur de chargement',
    },
  },
}

export default meta
type Story = StoryObj<typeof Button>

export const Primary: Story = {
  args: {
    children: 'Bouton Principal',
    variant: 'primary',
    size: 'md',
  },
}

export const Loading: Story = {
  args: {
    children: 'Sauvegarde en cours...',
    variant: 'primary',
    isLoading: true,
  },
}
```

### 5.3. Processus de Développement (CDD)
1. Créer ou modifier le composant dans son sous-dossier avec sa Story Storybook.
2. Vérifier visuellement tous ses états dans Storybook (états par défaut, survol, désactivé, chargement, erreur, responsive).
3. Intégrer ensuite le composant dans la molécule, l'organisme ou la page parente.
