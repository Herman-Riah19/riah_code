import type { Meta, StoryObj } from '@storybook/react'
import { Sidebar } from './Sidebar'
import type { SidebarItem, SidebarUser } from './Sidebar'

const meta: Meta<typeof Sidebar> = {
  title: 'Organisms/Sidebar',
  component: Sidebar,
  parameters: { layout: 'padded' },
  tags: ['autodocs'],
  argTypes: {},
}

export default meta
type Story = StoryObj<typeof Sidebar>

const mockItems: SidebarItem[] = [
  { id: 'corpus', label: 'Corpus', icon: 'database-icon', href: '/corpus' },
  { id: 'training', label: 'Entrainement', icon: 'play-icon', href: '/training' },
  { id: 'inference', label: 'Inference', icon: 'github-icon', href: '/inference' },
  { id: 'dashboard', label: 'Tableau de bord', icon: 'dashboard-icon', href: '/' },
]

const mockUser: SidebarUser = {
  name: 'Marie Dupont',
  email: 'marie.dupont@riah-code.local',
}

export const Default: Story = {
  args: {
    items: mockItems,
    activeItem: 'corpus',
    brand: 'Riah Code',
    user: mockUser,
  },
}

export const Collapsed: Story = {
  args: {
    items: mockItems,
    activeItem: 'corpus',
    brand: 'Riah Code',
    collapsed: true,
    user: mockUser,
  },
}

export const WithManyItems: Story = {
  args: {
    items: [
      ...mockItems,
      { id: 'settings', label: 'Parametres', icon: 'settings-icon', href: '/settings' },
      { id: 'profile', label: 'Profil', icon: 'user-icon', href: '/profile' },
      { id: 'billing', label: 'Facturation', icon: 'credit-card-icon', href: '/billing' },
    ],
    activeItem: 'dashboard',
    brand: 'Riah Code',
    user: mockUser,
  },
}

export const WithoutUser: Story = {
  args: {
    items: mockItems,
    activeItem: 'corpus',
    brand: 'Riah Code',
  },
} as Story
