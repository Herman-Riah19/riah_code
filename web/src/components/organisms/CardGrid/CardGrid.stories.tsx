import type { Meta, StoryObj } from '@storybook/react'
import { CardGrid } from './CardGrid'

const meta: Meta<typeof CardGrid> = {
  title: 'Organisms/CardGrid',
  component: CardGrid,
  parameters: { layout: 'padded' },
  tags: ['autodocs'],
  argTypes: {
    onItemClick: { action: 'itemClicked' },
    emptyAction: { action: 'emptyActionClicked' },
  },
}

export default meta
type Story = StoryObj<typeof CardGrid>

const mockDatasets = [
  {
    source: 'wikipedia',
    languages: ['fr', 'en'],
    documentCount: 12543,
    totalSizeBytes: 125829120,
    updatedAt: new Date().toISOString(),
    path: 'data/corpus/markdown/wikipedia',
  },
  {
    source: 'bible_gateway',
    languages: ['fr', 'en'],
    documentCount: 66,
    totalSizeBytes: 4194304,
    updatedAt: new Date(Date.now() - 86400000).toISOString(),
    path: 'data/corpus/markdown/bible_gateway',
  },
  {
    source: 'common_crawl',
    languages: ['en'],
    documentCount: 50000,
    totalSizeBytes: 1073741824,
    updatedAt: new Date(Date.now() - 172800000).toISOString(),
    path: 'data/corpus/markdown/common_crawl',
  },
]

export const WithData: Story = {
  args: { items: mockDatasets },
}

export const WithClick: Story = {
  args: { items: mockDatasets, onItemClick: (d) => alert(`Clicked: ${d.source}`) },
}

export const SingleItem: Story = {
  args: { items: mockDatasets.slice(0, 1) },
}

export const Empty: Story = {
  args: {
    items: [],
    emptyTitle: 'Aucun corpus',
    emptyDescription: 'Commencez par scraper des donnees.',
    emptyAction: { label: 'Demarrer', onClick: () => alert('Demarrer!') },
  },
}

export const ManyItems: Story = {
  args: {
    items: Array.from({ length: 12 }, (_, i) => ({
      ...mockDatasets[i % 3],
      source: `source_${i}`,
      documentCount: (i + 1) * 1000,
    })),
  },
}