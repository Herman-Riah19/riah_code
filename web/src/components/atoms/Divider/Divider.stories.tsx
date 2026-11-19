import type { Meta, StoryObj } from '@storybook/react'
import { Divider } from './Divider'
import { Stack } from '../Stack/Stack'
import { Box } from '../Box/Box'
import { Text } from '../Text/Text'

const meta: Meta<typeof Divider> = {
  title: 'Atoms/Divider',
  component: Divider,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    orientation: {
      control: 'select',
      options: ['horizontal', 'vertical'],
      description: 'Orientation du séparateur',
    },
    variant: {
      control: 'select',
      options: ['subtle', 'default', 'accent'],
      description: 'Style visuel du séparateur',
    },
    spacing: {
      control: 'select',
      options: ['none', 'sm', 'md', 'lg'],
      description: 'Marge autour du séparateur',
    },
  },
}

export default meta
type Story = StoryObj<typeof Divider>

export const DefaultHorizontal: Story = {
  args: {
    orientation: 'horizontal',
    variant: 'default',
    spacing: 'md',
  },
}

export const Subtle: Story = {
  args: {
    orientation: 'horizontal',
    variant: 'subtle',
    spacing: 'md',
  },
}

export const Accent: Story = {
  args: {
    orientation: 'horizontal',
    variant: 'accent',
    spacing: 'md',
  },
}

export const Vertical: Story = {
  args: {
    orientation: 'vertical',
    variant: 'default',
    spacing: 'md',
  },
}

export const BetweenSections: Story = {
  render: () => (
    <Stack spacing="lg">
      <Box padding="md" borderRadius="md" border="subtle" background="default">
        <Text size="sm" weight="medium">
          Section au-dessus du séparateur
        </Text>
      </Box>
      <Divider orientation="horizontal" variant="subtle" spacing="lg" />
      <Box padding="md" borderRadius="md" border="subtle" background="default">
        <Text size="sm" weight="medium">
          Section en-dessous du séparateur
        </Text>
      </Box>
    </Stack>
  ),
  args: {
    orientation: 'horizontal',
    variant: 'subtle',
    spacing: 'lg',
  },
}
