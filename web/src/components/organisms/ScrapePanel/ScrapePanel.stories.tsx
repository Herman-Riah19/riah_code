import type { Meta, StoryObj } from '@storybook/react'
import { ScrapePanel } from './ScrapePanel'
import type { ScrapeSource } from '@/types/corpus'

const meta: Meta<typeof ScrapePanel> = {
  title: 'Organisms/ScrapePanel',
  component: ScrapePanel,
  parameters: { layout: 'padded' },
  tags: ['autodocs'],
  argTypes: {
    onSourcesChange: { action: 'sourcesChanged' },
    onLanguageChange: { action: 'languageChanged' },
    onMaxDocumentsChange: { action: 'maxDocumentsChanged' },
    onStart: { action: 'startClicked' },
  },
}

export default meta
type Story = StoryObj<typeof ScrapePanel>

const mockSources: ScrapeSource[] = [
  { id: 'wikipedia', label: 'Wikipedia', description: 'Articles encyclopediques', languages: ['fr', 'en', 'es', 'de'] },
  { id: 'bible_gateway', label: 'Bible', description: 'Chapitres bibliques', languages: ['fr', 'en'] },
  { id: 'common_crawl', label: 'Common Crawl', description: 'Archive web massive', languages: ['en'] },
]

export const Default: Story = {
  args: {
    sources: mockSources,
    selectedSources: ['wikipedia'],
    language: 'fr',
    availableLanguages: ['fr', 'en'],
    maxDocuments: 1000,
    isStarting: false,
    onSourcesChange: () => {},
    onLanguageChange: () => {},
    onMaxDocumentsChange: () => {},
    onStart: () => {},
  },
}

export const MultipleSources: Story = {
  args: {
    sources: mockSources,
    selectedSources: ['wikipedia', 'bible_gateway'],
    language: 'fr',
    availableLanguages: ['fr', 'en'],
    maxDocuments: 5000,
    isStarting: false,
    onSourcesChange: () => {},
    onLanguageChange: () => {},
    onMaxDocumentsChange: () => {},
    onStart: () => {},
  },
}

export const Starting: Story = {
  args: {
    sources: mockSources,
    selectedSources: ['wikipedia'],
    language: 'fr',
    availableLanguages: ['fr', 'en'],
    maxDocuments: 1000,
    isStarting: true,
    onSourcesChange: () => {},
    onLanguageChange: () => {},
    onMaxDocumentsChange: () => {},
    onStart: () => {},
  },
}

export const Disabled: Story = {
  args: {
    sources: mockSources,
    selectedSources: ['wikipedia'],
    language: 'fr',
    availableLanguages: ['fr', 'en'],
    maxDocuments: 1000,
    isStarting: false,
    isDisabled: true,
    onSourcesChange: () => {},
    onLanguageChange: () => {},
    onMaxDocumentsChange: () => {},
    onStart: () => {},
  },
}

export const NoSourceSelected: Story = {
  args: {
    sources: mockSources,
    selectedSources: [],
    language: 'fr',
    availableLanguages: ['fr', 'en'],
    maxDocuments: 1000,
    isStarting: false,
    onSourcesChange: () => {},
    onLanguageChange: () => {},
    onMaxDocumentsChange: () => {},
    onStart: () => {},
  },
}

export const CustomLanguages: Story = {
  args: {
    sources: mockSources,
    selectedSources: ['wikipedia'],
    language: 'es',
    availableLanguages: ['fr', 'en', 'es', 'de', 'it', 'pt'],
    maxDocuments: 2000,
    isStarting: false,
    onSourcesChange: () => {},
    onLanguageChange: () => {},
    onMaxDocumentsChange: () => {},
    onStart: () => {},
  },
}