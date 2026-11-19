import type { Meta, StoryObj } from '@storybook/react'
import { Navbar } from './Navbar'

const meta: Meta<typeof Navbar> = {
  title: 'Organisms/Navbar',
  component: Navbar,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
  args: {
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
}

export default meta
type Story = StoryObj<typeof Navbar>

export const Default: Story = {}

export const WithoutBadge: Story = {
  args: {
    badge: undefined,
  },
}

export const Minimal: Story = {
  args: {
    links: [{ label: 'Accueil', href: '#', isActive: true }],
    actions: [{ label: 'Essai gratuit', variant: 'outline' }],
  },
}

export const NoActions: Story = {
  args: {
    actions: [],
  },
}
