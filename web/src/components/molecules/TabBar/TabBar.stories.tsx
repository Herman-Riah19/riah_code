import type { Meta, StoryObj } from '@storybook/react'
import { useState } from 'react'
import { TabBar, type TabBarItem } from './TabBar'

const meta: Meta<typeof TabBar> = {
  title: 'Molecules/TabBar',
  component: TabBar,
  parameters: { layout: 'padded' },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof TabBar>

const ITEMS: TabBarItem[] = [
  { id: 'preview', label: 'Aperçu', icon: 'dashboard-icon' },
  { id: 'info', label: 'Informations', icon: 'info-icon' },
  { id: 'train', label: 'Entraînement', icon: 'database-icon' },
  { id: 'encode', label: 'Encodage', icon: 'file-text-icon' },
  { id: 'tokens', label: 'Tokens', icon: 'hash-icon' },
]

const NO_ICONS: TabBarItem[] = [
  { id: 'one', label: 'Premier' },
  { id: 'two', label: 'Deuxième' },
  { id: 'three', label: 'Troisième' },
]

const ControlledDemo = ({
  items,
  initialId,
}: {
  items: TabBarItem[]
  initialId: string
}) => {
  const [activeId, setActiveId] = useState(initialId)
  return <TabBar items={items} activeId={activeId} onChange={setActiveId} />
}

export const Default: Story = {
  render: () => <ControlledDemo items={ITEMS} initialId="preview" />,
}

export const WithoutIcons: Story = {
  render: () => <ControlledDemo items={NO_ICONS} initialId="one" />,
}

export const SingleTab: Story = {
  render: () => (
    <ControlledDemo items={[{ id: 'only', label: 'Unique' }]} initialId="only" />
  ),
}
