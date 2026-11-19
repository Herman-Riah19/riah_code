import type { Meta, StoryObj } from '@storybook/react'
import { Input } from './Input'
import { Text } from '../Text/Text'

const meta: Meta<typeof Input> = {
  title: 'Atoms/Input',
  component: Input,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Taille du champ',
    },
    variant: {
      control: 'select',
      options: ['default', 'error', 'success'],
      description: 'État de validation',
    },
    isFullWidth: {
      control: 'boolean',
      description: 'Champ sur toute la largeur',
    },
    disabled: {
      control: 'boolean',
      description: 'Champ désactivé',
    },
    readOnly: {
      control: 'boolean',
      description: 'Champ en lecture seule',
    },
    placeholder: {
      control: 'text',
      description: 'Texte d’espace réservé',
    },
  },
}

export default meta
type Story = StoryObj<typeof Input>

export const Default: Story = {
  args: {
    size: 'md',
    variant: 'default',
    placeholder: 'Entrez du texte…',
    children: undefined,
  },
}

export const Sizes: Story = {
  args: {
    size: 'sm',
    variant: 'default',
    placeholder: 'Champ de taille sm',
  },
}

export const Large: Story = {
  args: {
    size: 'lg',
    variant: 'default',
    placeholder: 'Champ de taille lg',
  },
}

export const Error: Story = {
  args: {
    size: 'md',
    variant: 'error',
    placeholder: 'Champ en erreur',
  },
}

export const Success: Story = {
  args: {
    size: 'md',
    variant: 'success',
    placeholder: 'Champ validé',
  },
}

export const Disabled: Story = {
  args: {
    size: 'md',
    variant: 'default',
    placeholder: 'Champ désactivé',
    disabled: true,
  },
}

export const ReadOnly: Story = {
  args: {
    size: 'md',
    variant: 'default',
    placeholder: 'Lecture seule',
    readOnly: true,
    defaultValue: 'Valeur prédéfinie',
  },
}

export const FullWidth: Story = {
  args: {
    size: 'md',
    variant: 'default',
    placeholder: 'Champ sur toute la largeur',
    isFullWidth: true,
  },
}

export const WithLabel: Story = {
  args: {
    size: 'md',
    variant: 'default',
    placeholder: 'Votre nom',
    children: (
      <Text size="sm" weight="medium" color="emphasis" as="label" htmlFor="name-input">
        Nom complet
      </Text>
    ),
  },
}
