import type { Meta, StoryObj } from '@storybook/react'
import { TokenizerPreviewPanel } from './TokenizerPreviewPanel'
import type { TokenPreview } from '@/types/tokenizer'

const meta: Meta<typeof TokenizerPreviewPanel> = {
  title: 'Organisms/TokenizerPreviewPanel',
  component: TokenizerPreviewPanel,
  parameters: { layout: 'padded' },
  tags: ['autodocs'],
  argTypes: {
    onPreview: { action: 'previewClicked' },
    onClear: { action: 'clearClicked' },
  },
  args: {
    preview: null,
    isPreviewing: false,
    error: null,
    defaultText: 'Le petit chat dort sur le tapis.',
  },
}

export default meta
type Story = StoryObj<typeof TokenizerPreviewPanel>

const preview: TokenPreview = {
  text: 'Le petit chat dort sur le tapis.',
  tokenCount: 9,
  characterCount: 31,
  compressionRatio: 3.44,
  tokens: ['Le', '␣petit', '␣chat', '␣dort', '␣sur', '␣le', '␣tapis', '.'],
  tokenIds: [412, 987, 1123, 654, 233, 412, 2890, 16],
  decoded: 'Le petit chat dort sur le tapis.',
}

export const Empty: Story = {}

export const WithResult: Story = {
  args: { preview },
}

export const Loading: Story = {
  args: { isPreviewing: true, isDisabled: true },
}

export const WithError: Story = {
  args: { error: 'Aucun tokenizer entraine n est disponible.' },
}
