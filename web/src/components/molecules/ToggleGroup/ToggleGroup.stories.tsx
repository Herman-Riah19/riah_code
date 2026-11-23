import type { Meta, StoryObj } from '@storybook/react'
import { ToggleGroup } from './ToggleGroup'

const meta: Meta<typeof ToggleGroup> = {
  title: 'Molecules/ToggleGroup',
  component: ToggleGroup,
  parameters: { layout: 'centered' },
  tags: ['autodocs'],
  argTypes: {
    multiple: { control: 'boolean', description: 'Selection multiple autorisee' },
    isDisabled: { control: 'boolean', description: 'Desactive le groupe' },
  },
}

export default meta
type Story = StoryObj<typeof ToggleGroup>

const sources = [
  { value: 'wikipedia', label: 'Wikipedia' },
  { value: 'bible_gateway', label: 'Bible' },
  { value: 'common_crawl', label: 'Common Crawl' },
  { value: 'openwebtext', label: 'OpenWebText' },
]

export const SingleSelection: Story = {
  args: {
    options: sources,
    value: ['wikipedia'],
    multiple: false,
  },
}

export const MultipleSelection: Story = {
  args: {
    options: sources,
    value: ['wikipedia', 'bible_gateway'],
    multiple: true,
  },
}

export const Disabled: Story = {
  args: {
    options: sources,
    value: ['wikipedia'],
    isDisabled: true,
  },
}

export const TwoOptions: Story = {
  args: {
    options: sources.slice(0, 2),
    value: ['wikipedia'],
    multiple: true,
  },
}