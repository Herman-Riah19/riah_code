import type { Meta, StoryObj } from '@storybook/react'
import { SearchBar } from './SearchBar'

const meta: Meta<typeof SearchBar> = {
  title: 'Molecules/SearchBar',
  component: SearchBar,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    placeholder: {
      control: 'text',
      description: 'Texte d’espace réservé',
    },
  },
}

export default meta
type Story = StoryObj<typeof SearchBar>

export const Default: Story = {
  args: {
    placeholder: 'Rechercher…',
  },
}
