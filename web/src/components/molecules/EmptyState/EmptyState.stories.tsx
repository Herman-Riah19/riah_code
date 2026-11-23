import type { Meta, StoryObj } from '@storybook/react'
import { EmptyState } from './EmptyState'

const meta: Meta<typeof EmptyState> = {
  title: 'Molecules/EmptyState',
  component: EmptyState,
  parameters: { layout: 'centered' },
  tags: ['autodocs'],
  argTypes: {},
}

export default meta
type Story = StoryObj<typeof EmptyState>

export const Default: Story = {
  args: {
    title: 'Aucun corpus disponible',
    description: 'Commencez par scraper des donnees pour voir vos corpus ici.',
    actions: [
      { label: 'Demarrer le scraping', onClick: () => alert('Demarrer!'), variant: 'primary' },
    ],
  },
}

export const NoIcon: Story = {
  args: {
    title: 'Aucun resultat',
    description: 'Votre recherche n\'a retourne aucun resultat.',
    icon: undefined,
  },
}

export const WithSecondaryAction: Story = {
  args: {
    title: 'Aucune donnee',
    description: 'Il n\'y a pas encore de corpus pour cette source.',
    actions: [
      { label: 'Creer un corpus', onClick: () => alert('Creer!'), variant: 'primary' },
      { label: 'Importer', onClick: () => alert('Importer!'), variant: 'outline' },
    ],
  },
}