import type { Meta, StoryObj } from '@storybook/react'
import { Badge } from './Badge'

const meta: Meta<typeof Badge> = {
  title: 'Atoms/Badge',
  component: Badge,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'accent', 'success', 'warning', 'error', 'muted'],
      description: 'Variante visuelle du badge',
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Taille du badge',
    },
    dot: {
      control: 'boolean',
      description: 'Affiche un petit point (indicateur)',
    },
  },
}

export default meta
type Story = StoryObj<typeof Badge>

export const Default: Story = {
  args: {
    variant: 'default',
    size: 'md',
    dot: false,
    children: 'Défaut',
  },
}

export const Accent: Story = {
  args: {
    variant: 'accent',
    size: 'md',
    children: 'Accent',
  },
}

export const Success: Story = {
  args: {
    variant: 'success',
    size: 'md',
    children: 'Succès',
  },
}

export const Warning: Story = {
  args: {
    variant: 'warning',
    size: 'md',
    children: 'Attention',
  },
}

export const Error: Story = {
  args: {
    variant: 'error',
    size: 'md',
    children: 'Erreur',
  },
}

export const Muted: Story = {
  args: {
    variant: 'muted',
    size: 'md',
    children: 'Muet',
  },
}

export const Sizes: Story = {
  args: {
    variant: 'accent',
    size: 'sm',
    children: 'Petit',
  },
}

export const Dot: Story = {
  args: {
    variant: 'accent',
    size: 'sm',
    dot: true,
    children: 'Nouveau',
  },
}

export const AllVariants: Story = {
  args: {
    variant: 'default',
    size: 'md',
    dot: false,
    children: (
      <>
        <Badge variant="default" size="md" style={{ marginRight: '8px' }}>
          Défaut
        </Badge>
        <Badge variant="accent" size="md" style={{ marginRight: '8px' }}>
          Accent
        </Badge>
        <Badge variant="success" size="md" style={{ marginRight: '8px' }}>
          Succès
        </Badge>
        <Badge variant="warning" size="md" style={{ marginRight: '8px' }}>
          Attention
        </Badge>
        <Badge variant="error" size="md" style={{ marginRight: '8px' }}>
          Erreur
        </Badge>
        <Badge variant="muted" size="md">
          Muet
        </Badge>
      </>
    ),
  },
}
