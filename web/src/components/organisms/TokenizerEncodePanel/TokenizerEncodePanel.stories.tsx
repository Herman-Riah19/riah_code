import type { Meta, StoryObj } from '@storybook/react'
import { TokenizerEncodePanel } from './TokenizerEncodePanel'

const meta: Meta<typeof TokenizerEncodePanel> = {
  title: 'Organisms/TokenizerEncodePanel',
  component: TokenizerEncodePanel,
  parameters: { layout: 'padded' },
  tags: ['autodocs'],
  argTypes: {
    onShardSizeTokensChange: { action: 'shardSizeChanged' },
    onLanguagesChange: { action: 'languagesChanged' },
    onEncode: { action: 'encodeClicked' },
  },
  args: {
    shardSizeTokens: 5000000,
    languages: [],
    availableLanguages: ['fr', 'en', 'es', 'de'],
    hasTokenizer: true,
    isStarting: false,
  },
}

export default meta
type Story = StoryObj<typeof TokenizerEncodePanel>

export const Default: Story = {}

export const WithoutTokenizer: Story = {
  args: { hasTokenizer: false },
}

export const Starting: Story = {
  args: { isStarting: true, isDisabled: true },
}

export const FilteredLanguages: Story = {
  args: { languages: ['fr', 'en'] },
}

export const Disabled: Story = {
  args: { isDisabled: true },
}
