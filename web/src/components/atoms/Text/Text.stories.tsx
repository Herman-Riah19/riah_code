import type { Meta, StoryObj } from '@storybook/react'
import { Text } from './Text'

const meta: Meta<typeof Text> = {
  title: 'Atoms/Text',
  component: Text,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    as: {
      control: 'select',
      options: ['p', 'span', 'label', 'small', 'strong', 'em', 'li', 'div'],
      description: 'Balise HTML rendue sous-jacente',
    },
    size: {
      control: 'select',
      options: ['xs', 'sm', 'md', 'lg', 'xl'],
      description: 'Taille du texte',
    },
    weight: {
      control: 'select',
      options: ['normal', 'medium', 'semibold', 'bold'],
      description: 'Épaisseur de la police',
    },
    color: {
      control: 'select',
      options: ['default', 'muted', 'emphasis', 'accent', 'error', 'success', 'warning'],
      description: 'Couleur du texte',
    },
    align: {
      control: 'select',
      options: ['left', 'center', 'right'],
      description: 'Alignement du texte',
    },
    truncate: {
      control: 'boolean',
      description: 'Tronque le texte avec points de suspension',
    },
    mono: {
      control: 'boolean',
      description: 'Police à chasse fixe',
    },
  },
}

export default meta
type Story = StoryObj<typeof Text>

export const Default: Story = {
  args: {
    size: 'md',
    weight: 'normal',
    color: 'default',
    children: 'Ceci est un paragraphe de texte par défaut.',
  },
}

export const Sizes: Story = {
  args: {
    size: 'xs',
    color: 'muted',
    children: 'Texte de taille xs et couleur muted.',
  },
}

export const Weights: Story = {
  args: {
    size: 'md',
    weight: 'bold',
    color: 'emphasis',
    children: 'Texte en gras (weight bold) et accentué.',
  },
}

export const Colors: Story = {
  args: {
    size: 'md',
    color: 'accent',
    children: 'Texte de couleur accent.',
  },
}

export const Error: Story = {
  args: {
    size: 'sm',
    color: 'error',
    children: 'Message d’erreur en couleur error.',
  },
}

export const Success: Story = {
  args: {
    size: 'sm',
    color: 'success',
    children: 'Message de succès en couleur success.',
  },
}

export const Warning: Story = {
  args: {
    size: 'sm',
    color: 'warning',
    children: 'Message d’avertissement en couleur warning.',
  },
}

export const Alignments: Story = {
  args: {
    size: 'md',
    align: 'center',
    children: 'Texte centré.',
  },
}

export const Truncate: Story = {
  args: {
    size: 'md',
    truncate: true,
    children:
      'Ce texte est très long et doit être tronqué avec des points de suspension car il dépasse la largeur disponible du conteneur.',
  },
}

export const Mono: Story = {
  args: {
    size: 'sm',
    mono: true,
    children: 'Code monospace (mono).',
  },
}

export const Label: Story = {
  args: {
    as: 'label',
    size: 'sm',
    weight: 'medium',
    htmlFor: 'email-input',
    children: 'Adresse e-mail',
  },
}
