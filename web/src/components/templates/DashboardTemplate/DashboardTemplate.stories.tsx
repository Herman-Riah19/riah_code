import type { Meta, StoryObj } from '@storybook/react'
import { DashboardTemplate } from './DashboardTemplate'
import { Box } from '@/components/atoms/Box'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Icon } from '@/components/atoms/Icon'

const meta: Meta<typeof DashboardTemplate> = {
  title: 'Templates/DashboardTemplate',
  component: DashboardTemplate,
  parameters: { layout: 'fullscreen' },
  tags: ['autodocs'],
  argTypes: {},
}

export default meta
type Story = StoryObj<typeof DashboardTemplate>

export const Default: Story = {
  args: {
    navbar: {
      brand: 'Riah Code',
      badge: 'Dashboard',
      links: [
        { label: 'Corpus', href: '#/corpus', isActive: true },
        { label: 'Entrainement', href: '#/training' },
        { label: 'Inference', href: '#/inference' },
      ],
      actions: [
        { label: 'Profil', variant: 'ghost' },
        { label: 'Parametres', variant: 'outline' },
      ],
    },
    header: {
      eyebrow: 'Corpus',
      title: 'Tableau de bord Corpus',
      subtitle: 'Gerez et surveillez vos jeux de donnees d\'entrainement.',
      actions: [
        { label: 'Nouveau scraping', onClick: () => alert('New!'), variant: 'primary', leftIcon: <Icon name="plus-icon" size="sm" aria-hidden /> },
      ],
    },
    children: (
      <Box className="space-y-6">
        <Heading level={2} size="lg" weight="semibold" color="default">
          Vos corpus
        </Heading>
        <Text size="md" color="muted">
          Contenu de la page corpus ici...
        </Text>
      </Box>
    ),
  },
}

export const Minimal: Story = {
  args: {
    navbar: { brand: 'Riah Code', links: [] },
    header: { title: 'Page simple' },
    children: <Text>Contenu minimal</Text>,
  },
}

export const WithLongContent: Story = {
  args: {
    navbar: {
      brand: 'Riah Code',
      links: [
        { label: 'Accueil', href: '#/' },
        { label: 'Corpus', href: '#/corpus', isActive: true },
      ],
    },
    header: {
      title: 'Tableau de bord complet',
      subtitle: 'Description detaillee de la page avec beaucoup de texte pour tester le layout.',
    },
    children: (
      <Box className="space-y-8" style={{ minHeight: '800px' }}>
        <Heading level={2} size="xl" weight="bold" color="default">
          Section 1
        </Heading>
        <Box className="h-64 rounded-xl border border-border bg-card" />
        <Heading level={2} size="xl" weight="bold" color="default">
          Section 2
        </Heading>
        <Box className="h-64 rounded-xl border border-border bg-card" />
        <Heading level={2} size="xl" weight="bold" color="default">
          Section 3
        </Heading>
        <Box className="h-64 rounded-xl border border-border bg-card" />
      </Box>
    ),
  },
}