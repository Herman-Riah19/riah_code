import type { Meta, StoryObj } from '@storybook/react'
import { ResourceCard } from './ResourceCard'

const meta: Meta<typeof ResourceCard> = {
  title: 'Molecules/ResourceCard',
  component: ResourceCard,
  parameters: { layout: 'centered' },
  tags: ['autodocs'],
  argTypes: {
    onClick: { action: 'clicked' },
  },
}

export default meta
type Story = StoryObj<typeof ResourceCard>

const mockDataset = {
  source: 'wikipedia',
  languages: ['fr', 'en'],
  documentCount: 12543,
  totalSizeBytes: 125829120,
  updatedAt: new Date().toISOString(),
  path: 'data/corpus/markdown/wikipedia',
}

export const Default: Story = {
  args: { dataset: mockDataset },
}

export const Interactive: Story = {
  args: { dataset: mockDataset, onClick: () => alert('Card clicked!') },
}

export const SingleLanguage: Story = {
  args: { dataset: { ...mockDataset, languages: ['fr'], documentCount: 5000, totalSizeBytes: 52428800 } },
}

export const ManyLanguages: Story = {
  args: { dataset: { ...mockDataset, languages: ['fr', 'en', 'es', 'de', 'it', 'pt'], documentCount: 50000, totalSizeBytes: 524288000 } },
}

export const SmallDataset: Story = {
  args: { dataset: { ...mockDataset, languages: ['fr'], documentCount: 12, totalSizeBytes: 102400 } },
}