import type { Meta, StoryObj } from '@storybook/react'
import { Spinner } from './Spinner'

const meta: Meta<typeof Spinner> = {
  title: 'Atoms/Spinner',
  component: Spinner,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: 'select',
      options: ['xs', 'sm', 'md', 'lg', 'xl'],
      description: 'Taille du spinner',
    },
    color: {
      control: 'select',
      options: ['accent', 'default', 'white'],
      description: 'Couleur du spinner',
    },
    label: {
      control: 'text',
      description: 'Label d’accessibilité (aria-label)',
    },
  },
}

export default meta
type Story = StoryObj<typeof Spinner>

export const Default: Story = {
  args: {
    size: 'md',
    color: 'accent',
    label: 'Chargement...',
  },
}

export const XSmall: Story = {
  args: {
    size: 'xs',
    color: 'accent',
    label: 'Chargement...',
  },
}

export const Small: Story = {
  args: {
    size: 'sm',
    color: 'accent',
    label: 'Chargement...',
  },
}

export const Large: Story = {
  args: {
    size: 'lg',
    color: 'accent',
    label: 'Chargement...',
  },
}

export const ExtraLarge: Story = {
  args: {
    size: 'xl',
    color: 'accent',
    label: 'Chargement...',
  },
}

export const White: Story = {
  args: {
    size: 'md',
    color: 'white',
    label: 'Chargement...',
  },
}

export const DefaultColor: Story = {
  args: {
    size: 'md',
    color: 'default',
    label: 'Chargement...',
  },
}

export const CustomLabel: Story = {
  args: {
    size: 'md',
    color: 'accent',
    label: 'Chargement des données en cours…',
  },
}
