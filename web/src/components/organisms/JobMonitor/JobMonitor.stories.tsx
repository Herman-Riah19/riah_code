import type { Meta, StoryObj } from '@storybook/react'
import { JobMonitor } from './JobMonitor'
import type { JobConfigField, MonitorableJob } from '@/types/job'

const meta: Meta<typeof JobMonitor> = {
  title: 'Organisms/JobMonitor',
  component: JobMonitor,
  parameters: { layout: 'padded' },
  tags: ['autodocs'],
  argTypes: {
    onResume: { action: 'resumeClicked' },
    onDismiss: { action: 'dismissClicked' },
  },
  args: {
    title: 'Job de scraping',
    progressLabels: {
      documentsScraped: 'Documents scrapes',
      documentsCleaned: 'Documents nettoyes',
      documentsFiltered: 'Documents filtres',
      documentsDeduplicated: 'Documents dedupliques',
      documentsExported: 'Documents exportes (MD)',
      shardsWritten: 'Shards ecrits',
      totalTokens: 'Total tokens',
    },
    configFields: [
      { key: 'sources', label: 'Sources', icon: 'database-icon' },
      { key: 'languages', label: 'Langues', icon: 'globe-icon' },
      { key: 'maxArticlesPerLang', label: 'Max/doc', icon: 'file-text-icon' },
    ],
  },
}

export default meta
type Story = StoryObj<typeof JobMonitor>

const baseJob: MonitorableJob = {
  id: 'abc123-def456-ghi789',
  jobType: 'data_pipeline',
  status: 'running',
  config: {
    sources: ['wikipedia'],
    languages: ['fr'],
    maxArticlesPerLang: 1000,
    outputDir: 'data/corpus',
  },
  userId: 'user-1',
  createdAt: new Date(Date.now() - 300000).toISOString(),
  startedAt: new Date(Date.now() - 240000).toISOString(),
  finishedAt: null,
  progress: {
    documentsScraped: 850,
    documentsCleaned: 780,
    documentsFiltered: 45,
    documentsDeduplicated: 12,
    documentsExported: 723,
    shardsWritten: 1,
    totalTokens: 1250000,
  },
  error: null,
}

export const Running: Story = {
  args: {
    job: { ...baseJob, status: 'running' },
  },
}

export const Completed: Story = {
  args: {
    job: {
      ...baseJob,
      status: 'completed',
      finishedAt: new Date().toISOString(),
      progress: { ...baseJob.progress, documentsScraped: 1000, documentsCleaned: 920, documentsExported: 880 },
    },
    onDismiss: () => alert('Dismissed!'),
  },
}

export const Failed: Story = {
  args: {
    job: {
      ...baseJob,
      status: 'failed',
      finishedAt: new Date().toISOString(),
      error: 'Erreur de connexion a l\'API Wikipedia: timeout apres 30s',
    },
    onResume: () => alert('Resume!'),
  },
}

export const Pending: Story = {
  args: {
    job: {
      ...baseJob,
      status: 'pending',
      startedAt: null,
      progress: {},
    },
  },
}

export const Cancelled: Story = {
  args: {
    job: {
      ...baseJob,
      status: 'cancelled',
      finishedAt: new Date().toISOString(),
      progress: { ...baseJob.progress, documentsScraped: 200 },
    },
  },
}

export const NoProgress: Story = {
  args: {
    job: {
      ...baseJob,
      status: 'running',
      progress: {},
    },
  },
}

export const WithConfigOnly: Story = {
  args: {
    job: {
      ...baseJob,
      status: 'pending',
      progress: {},
      config: {
        sources: ['wikipedia', 'bible_gateway'],
        languages: ['fr', 'en'],
        maxArticlesPerLang: 5000,
        outputDir: 'data/corpus',
      },
    },
  },
}

const tokenizerConfigFields: JobConfigField[] = [
  { key: 'languages', label: 'Langues', icon: 'globe-icon' },
  { key: 'vocabSize', label: 'Taille du vocabulaire' },
  { key: 'minFrequency', label: 'Frequence minimale' },
  { key: 'corpusSampleSize', label: 'Echantillon corpus' },
]

export const TokenizerTraining: Story = {
  args: {
    title: "Job d'entrainement du tokenizer",
    progressLabels: {
      vocabSize: 'Taille du vocabulaire',
      compressionRatio: 'Compression (chars/token)',
      oovRate: 'Taux OOV',
    },
    configFields: tokenizerConfigFields,
    job: {
      id: 'tok-42f1-9c3d',
      jobType: 'tokenizer_training',
      status: 'completed',
      config: {
        languages: ['fr', 'en'],
        vocabSize: 32000,
        minFrequency: 2,
        corpusSampleSize: 20000,
      },
      userId: 'user-1',
      createdAt: new Date(Date.now() - 120000).toISOString(),
      startedAt: new Date(Date.now() - 115000).toISOString(),
      finishedAt: new Date().toISOString(),
      progress: {
        vocabSize: 32000,
        compressionRatio: 3.56,
        oovRate: 0,
      },
      error: null,
    },
    onDismiss: () => alert('Dismissed!'),
  },
}
