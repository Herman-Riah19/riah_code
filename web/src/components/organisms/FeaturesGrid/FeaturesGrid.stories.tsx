import type { Meta, StoryObj } from '@storybook/react'
import { FeaturesGrid } from './FeaturesGrid'

const meta: Meta<typeof FeaturesGrid> = {
  title: 'Organisms/FeaturesGrid',
  component: FeaturesGrid,
  tags: ['autodocs'],
  args: {
    eyebrow: 'Plateforme',
    title: 'Tout ce qu il faut pour vos modeles',
    subtitle: 'De la preparation du corpus au deploiement, un pipeline complet et unifie.',
    columns: 3,
    items: [
      {
        id: 'pipeline',
        icon: 'documentation-icon',
        title: 'Pipeline de donnees',
        description:
          'Nettoyage, tokenisation et splitting de votre corpus avec des controles de qualite integres.',
      },
      {
        id: 'training',
        icon: 'social-icon',
        title: 'Entrainement supervise',
        description:
          'Lancez vos runs Transformers, suivez les metriques en temps reel et comparez les versions.',
      },
      {
        id: 'inference',
        icon: 'github-icon',
        title: 'Inference souple',
        description:
          'Deployez vos checkpoints et servez des requetes via une API typee et securisee.',
      },
      {
        id: 'dashboard',
        icon: 'discord-icon',
        title: 'Tableau de bord',
        description:
          'Visualisez vos runs, vos couts et la sante de vos modeles depuis une interface unique.',
      },
      {
        id: 'collab',
        icon: 'x-icon',
        title: 'Collaboration',
        description: 'Partagez vos experiments et vos datasets avec toute votre equipe.',
      },
      {
        id: 'quality',
        icon: 'bluesky-icon',
        title: 'Qualite & tests',
        description: "Suite de tests automatiques et criteres d'acceptation pour chaque livraison.",
      },
    ],
  },
}

export default meta
type Story = StoryObj<typeof FeaturesGrid>

export const Default: Story = {}

export const TwoColumns: Story = {
  args: {
    columns: 2,
    items: [
      {
        id: 'a',
        icon: 'documentation-icon',
        title: 'Premier bloc',
        description: 'Une description courte pour valider la grille sur deux colonnes.',
      },
      {
        id: 'b',
        icon: 'github-icon',
        title: 'Second bloc',
        description: 'Un autre bloc symetrique pour completer la mise en page.',
      },
    ],
  },
}

export const WithoutEyebrow: Story = {
  args: {
    eyebrow: undefined,
    subtitle: undefined,
  },
}
