import type { Meta, StoryObj } from '@storybook/react'
import { PageHeader } from './PageHeader'
import { Icon } from '@/components/atoms/Icon'

const meta: Meta<typeof PageHeader> = {
  title: 'Organisms/PageHeader',
  component: PageHeader,
  parameters: { layout: 'padded' },
  tags: ['autodocs'],
  argTypes: {},
}

export default meta
type Story = StoryObj<typeof PageHeader>

export const Basic: Story = {
  args: {
    title: 'Tableau de bord Corpus',
    subtitle: 'Gerez et surveillez vos jeux de donnees d\'entrainement.',
  },
}

export const WithEyebrowAndBadge: Story = {
  args: {
    eyebrow: 'Corpus',
    title: 'Tableau de bord Corpus',
    subtitle: 'Gerez et surveillez vos jeux de donnees d\'entrainement.',
    badge: { variant: 'accent', label: 'Beta' },
  },
}

export const WithActions: Story = {
  args: {
    title: 'Tableau de bord Corpus',
    subtitle: 'Gerez et surveillez vos jeux de donnees d\'entrainement.',
    actions: [
      { label: 'Exporter', onClick: () => alert('Exporter!'), variant: 'outline' },
      { label: 'Nouveau scraping', onClick: () => alert('Scraper!'), variant: 'primary', leftIcon: <Icon name="download-icon" size="sm" aria-hidden /> },
    ],
  },
}

export const LoadingAction: Story = {
  args: {
    title: 'Traitement en cours',
    subtitle: 'Le scraping est en cours...',
    actions: [
      { label: 'Annuler', onClick: () => alert('Annuler!'), variant: 'outline' },
      { label: 'En cours...', onClick: () => {}, variant: 'primary', isLoading: true },
    ],
  },
}

export const LongTitle: Story = {
  args: {
    eyebrow: 'Gestion des donnees',
    title: 'Administration des corpus d\'entrainement pour modeles de langage',
    subtitle: 'Visualisez, creez et gerez vos jeux de donnees pour l\'entrainement et le fine-tuning de vos modeles.',
    actions: [
      { label: 'Creer un corpus', onClick: () => {}, variant: 'primary' },
      { label: 'Importer', onClick: () => {}, variant: 'outline' },
    ],
  },
}