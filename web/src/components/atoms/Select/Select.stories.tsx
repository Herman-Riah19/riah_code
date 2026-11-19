import type { Meta, StoryObj } from '@storybook/react'
import { Select } from './Select'
import { Box } from '../Box/Box'
import { Text } from '../Text/Text'

const meta: Meta<typeof Select> = {
  title: 'Atoms/Select',
  component: Select,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    className: {
      control: 'text',
      description: 'Classes CSS additionnelles',
    },
  },
}

export default meta
type Story = StoryObj<typeof Select>

export const Default: Story = {
  args: {
    children: (
      <>
        <option value="">Selectionnez une option</option>
        <option value="option1">Option 1</option>
        <option value="option2">Option 2</option>
        <option value="option3">Option 3</option>
      </>
    ),
  },
}

export const WithLabel: Story = {
  render: () => (
    <Box padding="md">
      <Box margin="md">
        <Text size="sm" weight="medium" color="default">
          Choisir une option
        </Text>
      </Box>
      <Select>
        <option value="">Selectionnez une option</option>
        <option value="option1">Option 1</option>
        <option value="option2">Option 2</option>
      </Select>
    </Box>
  ),
  args: {},
}

export const Disabled: Story = {
  args: {
    disabled: true,
    children: (
      <>
        <option value="">Desactive</option>
        <option value="option1">Option 1</option>
      </>
    ),
  },
}
