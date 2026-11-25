import type { Meta, StoryObj } from '@storybook/react'
import { TokenizerTokensTable } from './TokenizerTokensTable'
import type { TokenizerVocabEntry } from '@/types/tokenizer'

const meta: Meta<typeof TokenizerTokensTable> = {
  title: 'Organisms/TokenizerTokensTable',
  component: TokenizerTokensTable,
  parameters: { layout: 'padded' },
  tags: ['autodocs'],
  argTypes: {
    isLoading: { control: 'boolean' },
  },
}

export default meta
type Story = StoryObj<typeof TokenizerTokensTable>

const sampleTokens: TokenizerVocabEntry[] = [
  { token: 'Le', tokenId: 491 },
  { token: '␣petit', tokenId: 3251 },
  { token: 'chat', tokenId: 166 },
  { token: 'The', tokenId: 882 },
  { token: '␣model', tokenId: 1450 },
  { token: '.', tokenId: 12 },
]

export const Default: Story = {
  args: { tokens: sampleTokens },
}

export const Empty: Story = {
  args: { tokens: [] },
}

export const Loading: Story = {
  args: { tokens: [], isLoading: true },
}
