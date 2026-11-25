import type { Meta, StoryObj } from '@storybook/react'
import { CorpusTable } from './CorpusTable'
import type { CorpusFileInfo } from './CorpusTable'
import type { CorpusDataset } from '@/types/corpus'

const meta: Meta<typeof CorpusTable> = {
  title: 'Organisms/CorpusTable',
  component: CorpusTable,
  parameters: { layout: 'padded' },
  tags: ['autodocs'],
  argTypes: {
    onFileClick: { action: 'fileClicked' },
  },
}

export default meta
type Story = StoryObj<typeof CorpusTable>

const mockDataset: CorpusDataset = {
  source: 'wikipedia',
  languages: ['fr', 'en'],
  documentCount: 12543,
  totalSizeBytes: 125829120,
  updatedAt: new Date().toISOString(),
  path: 'data/corpus/markdown/wikipedia',
}

const mockFiles: CorpusFileInfo[] = Array.from({ length: 25 }, (_, i) => ({
  id: `file-${i}`,
  filename: `document_${i}.md`,
  source: i % 2 === 0 ? 'wikipedia' : 'bible_gateway',
  language: i % 2 === 0 ? 'fr' : 'en',
  sizeBytes: 738 + i * 100,
  tokenCount: 89 + i * 5,
  updatedAt: new Date(Date.now() - i * 3600000).toISOString(),
}))

export const WithData: Story = {
  args: {
    files: mockFiles,
    dataset: mockDataset,
    pageSize: 10,
  },
}

export const WithSearchAndPagination: Story = {
  args: {
    files: mockFiles,
    dataset: mockDataset,
    pageSize: 5,
  },
}

export const WithClick: Story = {
  args: {
    files: mockFiles.slice(0, 5),
    dataset: mockDataset,
    onFileClick: (file) => alert(`Ouvert: ${file.filename}`),
  },
}

export const Empty: Story = {
  args: {
    files: [],
    dataset: mockDataset,
  },
}

export const WithoutDataset: Story = {
  args: {
    files: mockFiles.slice(0, 5),
  },
}

export const SinglePage: Story = {
  args: {
    files: mockFiles.slice(0, 3),
    dataset: mockDataset,
    pageSize: 10,
  },
}
