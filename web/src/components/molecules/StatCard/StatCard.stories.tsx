import type { Meta, StoryObj } from '@storybook/react'
import { StatCard } from './StatCard'

const meta: Meta<typeof StatCard> = {
  title: 'Molecules/StatCard',
  component: StatCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    title: {
      control: 'text',
      description: 'Titre de la carte',
    },
    value: {
      control: 'text',
      description: 'Valeur affichée',
    },
  },
}

export default meta
type Story = StoryObj<typeof StatCard>

export const Default: Story = {
  args: {
    title: 'Entraînements actifs',
    value: '12',
    subtitle: 'Cette semaine',
  },
}

export const WithTrend: Story = {
  args: {
    title: 'Entraînements actifs',
    value: '12',
    subtitle: 'Cette semaine',
    trend: {
      value: '+12%',
      isPositive: true,
    },
  },
}

export const WithBadge: Story = {
  args: {
    title: 'Modèles déployés',
    value: '4',
    subtitle: 'En production',
    badge: {
      variant: 'success',
      label: 'Opérationnel',
    },
  },
}
