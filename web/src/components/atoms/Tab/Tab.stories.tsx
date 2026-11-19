import type { Meta, StoryObj } from '@storybook/react'
import { Tab } from './Tab'
import { Box } from '../Box/Box'

const meta: Meta<typeof Tab> = {
  title: 'Atoms/Tab',
  component: Tab,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    className: {
      control: 'text',
      description: 'Classes CSS additionnelles',
    },
    isActive: {
      control: 'boolean',
      description: 'Indique si longlet est actif',
    },
  },
}

export default meta
type Story = StoryObj<typeof Tab>

export const Default: Story = {
  args: {
    children: 'Onglet',
  },
}

export const Active: Story = {
  args: {
    isActive: true,
    children: 'Onglet actif',
  },
}

export const TabsGroup: Story = {
  render: () => (
    <Box>
      <Tab>Premier</Tab>
      <Tab isActive>Deuxieme</Tab>
      <Tab>Troisieme</Tab>
    </Box>
  ),
  args: {},
}
