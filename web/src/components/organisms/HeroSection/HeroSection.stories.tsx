import type { Meta, StoryObj } from '@storybook/react'
import { HeroSection } from './HeroSection'

const meta: Meta<typeof HeroSection> = {
  title: 'Organisms/HeroSection',
  component: HeroSection,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
  args: {
    badge: 'Nouveau : fine-tuning en 1 clic',
    title: 'Entrainez vos modeles de langage, sans friction',
    subtitle:
      'Riah Code est la plateforme complete pour preparer vos donnees, entrainer vos Transformers et deployer votre inference depuis un seul tableau de bord.',
    primaryAction: { label: 'Commencer gratuitement' },
    secondaryAction: { label: 'Lire la documentation', variant: 'outline' },
  },
}

export default meta
type Story = StoryObj<typeof HeroSection>

export const Default: Story = {}

export const WithoutBadge: Story = {
  args: {
    badge: undefined,
  },
}

export const SingleAction: Story = {
  args: {
    secondaryAction: undefined,
  },
}

export const Minimal: Story = {
  args: {
    badge: undefined,
    subtitle: undefined,
    secondaryAction: undefined,
  },
}
