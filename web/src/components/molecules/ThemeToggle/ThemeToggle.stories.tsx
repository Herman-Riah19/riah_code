import type { Meta, StoryObj } from '@storybook/react'
import { ThemeToggle } from './ThemeToggle'

const meta: Meta<typeof ThemeToggle> = {
  title: 'Molecules/ThemeToggle',
  component: ThemeToggle,
  parameters: { layout: 'centered' },
  tags: ['autodocs'],
  argTypes: {
    showLabel: {
      control: 'boolean',
      description: 'Affiche le libelle a cote de l icone',
    },
    className: {
      control: 'text',
      description: 'Classes additionnelles',
    },
  },
}

export default meta
type Story = StoryObj<typeof ThemeToggle>

export const IconOnly: Story = {
  args: {
    showLabel: false,
  },
}

export const WithLabel: Story = {
  args: {
    showLabel: true,
  },
}
