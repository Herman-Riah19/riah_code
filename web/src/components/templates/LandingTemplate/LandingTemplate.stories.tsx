import type { Meta, StoryObj } from '@storybook/react'
import { LandingTemplate } from './LandingTemplate'

const meta: Meta<typeof LandingTemplate> = {
  title: 'Templates/LandingTemplate',
  component: LandingTemplate,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
  args: {
    navbar: {
      brand: 'Riah Code',
      badge: 'Beta',
      links: [
        { label: 'Fonctionnalites', href: '#features', isActive: true },
        { label: 'Documentation', href: '#docs' },
        { label: 'Tarifs', href: '#pricing' },
      ],
      actions: [
        { label: 'Connexion', variant: 'ghost' },
        { label: 'Commencer', variant: 'primary' },
      ],
    },
    hero: {
      badge: 'Nouveau : fine-tuning en 1 clic',
      title: 'Entrainez vos modeles de langage, sans friction',
      subtitle:
        'Preparez vos donnees, lancez vos runs Transformers et servez votre inference depuis un seul tableau de bord.',
      primaryAction: { label: 'Commencer gratuitement' },
      secondaryAction: { label: 'Lire la documentation', variant: 'outline' },
    },
    features: {
      eyebrow: 'Plateforme',
      title: 'Tout ce qu il faut pour vos modeles',
      subtitle: 'De la preparation du corpus au deploiement, un pipeline complet et unifie.',
      columns: 3,
      items: [
        {
          id: 'pipeline',
          icon: 'documentation-icon',
          title: 'Pipeline de donnees',
          description: 'Nettoyage, tokenisation et splitting de votre corpus avec des controles de qualite.',
        },
        {
          id: 'training',
          icon: 'social-icon',
          title: 'Entrainement supervise',
          description: 'Lancez vos runs, suivez les metriques en temps reel et comparez les versions.',
        },
        {
          id: 'inference',
          icon: 'github-icon',
          title: 'Inference souple',
          description: 'Deployez vos checkpoints et servez des requetes via une API typee et securisee.',
        },
      ],
    },
    callToAction: {
      title: 'Pret a lancer votre premier run ?',
      description: 'Creez un compte, importez votre corpus et demarrez en quelques minutes.',
      primaryAction: { label: 'Commencer gratuitement' },
      secondaryAction: { label: 'Voir une demo', variant: 'outline' },
      note: 'Sans carte bancaire — annulable a tout moment.',
    },
    footer: {
      brand: 'Riah Code',
      columns: [
        {
          id: 'produit',
          title: 'Produit',
          links: [
            { label: 'Fonctionnalites', href: '#features' },
            { label: 'Tarifs', href: '#pricing' },
          ],
        },
        {
          id: 'ressources',
          title: 'Ressources',
          links: [
            { label: 'Documentation', href: '#docs' },
            { label: 'Guide API', href: '#api' },
          ],
        },
      ],
      socialLinks: [
        { label: 'GitHub', href: 'https://github.com' },
        { label: 'X', href: 'https://x.com' },
      ],
    },
  },
}

export default meta
type Story = StoryObj<typeof LandingTemplate>

export const Default: Story = {}

export const WithoutHero: Story = {
  args: {
    hero: undefined,
  },
}

export const Barebones: Story = {
  args: {
    navbar: { brand: 'Riah Code', links: [], actions: [] },
    hero: undefined,
    features: undefined,
    callToAction: undefined,
    footer: { brand: 'Riah Code', columns: [], socialLinks: [] },
  },
}
