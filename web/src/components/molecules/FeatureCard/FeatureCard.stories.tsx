import type { Meta, StoryObj } from '@storybook/react'
import { FeatureCard } from './FeatureCard'

const meta: Meta<typeof FeatureCard> = {
  title: 'Molecules/FeatureCard',
  component: FeatureCard,
  tags: ['autodocs'],
  args: {
    icon: 'documentation-icon',
    title: 'Pipeline de donnees',
    description:
      'Nettoyage, tokenisation et splitting de votre corpus avec des controles de qualite integres.',
  },
}

export default meta
type Story = StoryObj<typeof FeatureCard>

export const Default: Story = {}

export const WithoutIcon: Story = {
  args: {
    icon: undefined,
  },
}

export const LongContent: Story = {
  args: {
    icon: 'github-icon',
    title: 'Entrainement supervise de bout en bout',
    description:
      'Lancez vos runs Transformers, suivez les metriques en temps reel, comparez les versions et partagez vos experiments avec votre equipe depuis un tableau de bord unifie.',
  },
}
