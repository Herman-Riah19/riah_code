import type { Meta, StoryObj } from '@storybook/react'
import { Icon } from './Icon'
import { Box } from '../Box/Box'
import { Text as TextAtom } from '../Text/Text'

const meta: Meta<typeof Icon> = {
  title: 'Atoms/Icon',
  component: Icon,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    name: {
      control: 'text',
      description: "Nom de l'icône (alias lucide, ex. `settings`, `database-icon`)",
    },
    size: {
      control: 'select',
      options: ['xs', 'sm', 'md', 'lg', 'xl'],
      description: 'Taille de l’icône',
    },
    color: {
      control: 'select',
      options: ['default', 'muted', 'accent', 'error', 'success', 'warning', 'inherit'],
      description: 'Couleur de l’icône',
    },
    'aria-label': {
      control: 'text',
      description: 'Label d’accessibilité',
    },
    'aria-hidden': {
      control: 'boolean',
      description: 'Masquer aux lecteurs d’écran',
    },
  },
}

export default meta
type Story = StoryObj<typeof Icon>

export const Default: Story = {
  args: {
    name: 'settings',
    size: 'md',
    color: 'inherit',
    'aria-label': 'Réglages',
  },
}

export const Sizes: Story = {
  args: {
    name: 'settings',
    size: 'xs',
    color: 'accent',
    'aria-label': 'Icône petite',
  },
}

export const AccentColor: Story = {
  args: {
    name: 'settings',
    size: 'md',
    color: 'accent',
    'aria-label': 'Icône accent',
  },
}

export const ErrorColor: Story = {
  args: {
    name: 'alert',
    size: 'md',
    color: 'error',
    'aria-label': 'Erreur',
  },
}

export const SuccessColor: Story = {
  args: {
    name: 'check',
    size: 'md',
    color: 'success',
    'aria-label': 'Succès',
  },
}

export const Hidden: Story = {
  args: {
    name: 'settings',
    size: 'md',
    color: 'inherit',
    'aria-hidden': true,
  },
}

export const InToolbar: Story = {
  render: () => (
    <Box padding="sm" borderRadius="md" border="subtle" background="default">
      <Icon name="search" size="sm" color="muted" aria-label="Rechercher" />
      <TextAtom size="sm" color="default">
        Champ de recherche
      </TextAtom>
    </Box>
  ),
  args: {
    name: 'search',
    size: 'sm',
    color: 'muted',
    'aria-label': 'Rechercher',
  },
}
