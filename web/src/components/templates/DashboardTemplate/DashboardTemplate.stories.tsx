import type { Meta, StoryObj } from '@storybook/react'
import { DashboardTemplate } from './DashboardTemplate'
import { Box } from '@/components/atoms/Box'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'

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
    activeItem: 'corpus',
    brand: 'Riah Code',
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
    activeItem: 'dashboard',
    brand: 'Riah Code',
    children: <Text>Contenu minimal</Text>,
  },
}

export const WithCustomItems: Story = {
  args: {
    activeItem: 'training',
    brand: 'Riah Code',
    sidebarItems: [
      { id: 'corpus', label: 'Corpus', icon: 'database-icon', href: '/corpus' },
      { id: 'training', label: 'Entrainement', icon: 'play-icon', href: '/training' },
      { id: 'settings', label: 'Parametres', icon: 'settings-icon', href: '/settings' },
    ],
    children: (
      <Box className="space-y-6">
        <Heading level={2} size="lg" weight="semibold" color="default">
          Entrainement
        </Heading>
      </Box>
    ),
  },
}