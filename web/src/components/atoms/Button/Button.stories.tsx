import type { Meta, StoryObj } from '@storybook/react'
import { Button } from './Button'
import { Spinner } from '../Spinner/Spinner'
import { Icon } from '../Icon/Icon'

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
      control: 'select',
      options: ['xs', 'sm', 'md', 'lg'],
      description: 'Taille du bouton',
    },
    isLoading: {
      control: 'boolean',
      description: 'Affiche un indicateur de chargement',
    },
    isFullWidth: {
      control: 'boolean',
      description: 'Bouton sur toute la largeur',
    },
    disabled: {
      control: 'boolean',
      description: 'Désactive le bouton',
    },
  },
}

export default meta
type Story = StoryObj<typeof Button>

export const Primary: Story = {
  args: {
    children: 'Bouton principal',
    variant: 'primary',
    size: 'md',
  },
}

export const Secondary: Story = {
  args: {
    children: 'Secondaire',
    variant: 'secondary',
    size: 'md',
  },
}

export const Outline: Story = {
  args: {
    children: 'Contour',
    variant: 'outline',
    size: 'md',
  },
}

export const Ghost: Story = {
  args: {
    children: 'Fantôme',
    variant: 'ghost',
    size: 'md',
  },
}

export const Danger: Story = {
  args: {
    children: 'Supprimer',
    variant: 'danger',
    size: 'md',
  },
}

export const Sizes: Story = {
  args: {
    children: 'Taille',
    variant: 'primary',
    size: 'sm',
  },
}

export const Loading: Story = {
  args: {
    children: 'Sauvegarde en cours...',
    variant: 'primary',
    size: 'md',
    isLoading: true,
  },
}

export const Disabled: Story = {
  args: {
    children: 'Désactivé',
    variant: 'primary',
    size: 'md',
    disabled: true,
  },
}

export const FullWidth: Story = {
  args: {
    children: 'Largeur complète',
    variant: 'primary',
    size: 'md',
    isFullWidth: true,
  },
}

export const WithLeftIcon: Story = {
  args: {
    children: 'Avec icône à gauche',
    variant: 'primary',
    size: 'md',
    leftIcon: <Icon name="settings" size="sm" aria-label="Réglages" />,
  },
}

export const WithRightIcon: Story = {
  args: {
    children: 'Avec icône à droite',
    variant: 'outline',
    size: 'md',
    rightIcon: <Icon name="arrow-right" size="sm" aria-label="Suivant" />,
  },
}

export const WithSpinner: Story = {
  args: {
    children: 'Chargement...',
    variant: 'primary',
    size: 'md',
    isLoading: true,
    leftIcon: <Spinner size="xs" color="white" label="Chargement" />,
  },
}
