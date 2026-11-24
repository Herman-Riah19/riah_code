import type { Meta, StoryObj } from '@storybook/react'
import { TokenizerInfoPanel } from './TokenizerInfoPanel'
import type { TokenizerVocabInfo } from '@/types/tokenizer'

const meta: Meta<typeof TokenizerInfoPanel> = {
  title: 'Organisms/TokenizerInfoPanel',
  component: TokenizerInfoPanel,
  parameters: { layout: 'padded' },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof TokenizerInfoPanel>

const info: TokenizerVocabInfo = {
  vocabSize: 32000,
  specialTokenIds: {
    '<|endoftext|>': 0,
    '<|pad|>': 1,
    '<|unk|>': 2,
    '<|mask|>': 3,
  },
  compressionRatio: 3.56,
  oovRate: 0,
  trainedAt: new Date(Date.now() - 3600000).toISOString(),
  configHash: '7b56349bb895ea25',
}

export const WithInfo: Story = {
  args: { info },
}

export const Empty: Story = {
  args: { info: null },
}

export const Loading: Story = {
  args: { info: null, isLoading: true },
}

export const HighOov: Story = {
  args: {
    info: {
      ...info,
      vocabSize: 4000,
      compressionRatio: 2.31,
      oovRate: 0.084,
    },
  },
}
