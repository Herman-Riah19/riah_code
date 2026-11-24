import type { Meta, StoryObj } from '@storybook/react'
import { TokenizerTrainPanel } from './TokenizerTrainPanel'

const meta: Meta<typeof TokenizerTrainPanel> = {
  title: 'Organisms/TokenizerTrainPanel',
  component: TokenizerTrainPanel,
  parameters: { layout: 'padded' },
  tags: ['autodocs'],
  argTypes: {
    onVocabSizeChange: { action: 'vocabSizeChanged' },
    onMinFrequencyChange: { action: 'minFrequencyChanged' },
    onCorpusSampleSizeChange: { action: 'corpusSampleSizeChanged' },
    onNumThreadsChange: { action: 'numThreadsChanged' },
    onLanguagesChange: { action: 'languagesChanged' },
    onTrain: { action: 'trainClicked' },
  },
  args: {
    vocabSize: 32000,
    minFrequency: 2,
    corpusSampleSize: 20000,
    numThreads: 4,
    languages: ['fr'],
    availableLanguages: ['fr', 'en', 'es', 'de'],
    isStarting: false,
  },
}

export default meta
type Story = StoryObj<typeof TokenizerTrainPanel>

export const Default: Story = {}

export const Starting: Story = {
  args: { isStarting: true, isDisabled: true },
}

export const Multilingual: Story = {
  args: { languages: ['fr', 'en'] },
}

export const NoLanguageSelected: Story = {
  args: { languages: [] },
}

export const Disabled: Story = {
  args: { isDisabled: true },
}
