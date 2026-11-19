import type { Meta, StoryObj } from '@storybook/react'
import { Stack } from './Stack'
import { Box } from '../Box/Box'
import { Text } from '../Text/Text'
import { Button } from '../Button/Button'

const meta: Meta<typeof Stack> = {
  title: 'Atoms/Stack',
  component: Stack,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    direction: {
      control: 'select',
      options: ['vertical', 'horizontal'],
      description: 'Direction de l’empilement',
    },
    spacing: {
      control: 'select',
      options: ['none', 'xs', 'sm', 'md', 'lg', 'xl'],
      description: 'Espacement entre les enfants',
    },
  },
}

export default meta
type Story = StoryObj<typeof Stack>

export const DefaultVertical: Story = {
  args: {
    direction: 'vertical',
    spacing: 'md',
    children: (
      <>
        <Box padding="sm" borderRadius="md" border="subtle" background="default">
          <Text size="sm" weight="medium">
            Premier élément
          </Text>
        </Box>
        <Box padding="sm" borderRadius="md" border="subtle" background="default">
          <Text size="sm" weight="medium">
            Deuxième élément
          </Text>
        </Box>
        <Box padding="sm" borderRadius="md" border="subtle" background="default">
          <Text size="sm" weight="medium">
            Troisième élément
          </Text>
        </Box>
      </>
    ),
  },
}

export const Horizontal: Story = {
  args: {
    direction: 'horizontal',
    spacing: 'sm',
    children: (
      <>
        <Box padding="sm" borderRadius="md" border="subtle" background="default">
          <Text size="sm" weight="medium">Un</Text>
        </Box>
        <Box padding="sm" borderRadius="md" border="subtle" background="default">
          <Text size="sm" weight="medium">Deux</Text>
        </Box>
        <Box padding="sm" borderRadius="md" border="subtle" background="default">
          <Text size="sm" weight="medium">Trois</Text>
        </Box>
      </>
    ),
  },
}

export const SmallSpacing: Story = {
  args: {
    direction: 'vertical',
    spacing: 'xs',
    children: (
      <>
        <Box padding="xs" borderRadius="sm" border="subtle" background="muted">
          <Text size="xs" color="muted">Espacement xs</Text>
        </Box>
        <Box padding="xs" borderRadius="sm" border="subtle" background="muted">
          <Text size="xs" color="muted">Très rapprochés</Text>
        </Box>
      </>
    ),
  },
}

export const LargeSpacing: Story = {
  args: {
    direction: 'vertical',
    spacing: 'xl',
    children: (
      <>
        <Box padding="md" borderRadius="md" border="subtle" background="default">
          <Text size="md">Élément espacé</Text>
        </Box>
        <Box padding="md" borderRadius="md" border="subtle" background="default">
          <Text size="md">Grand écart (xl)</Text>
        </Box>
      </>
    ),
  },
}

export const WithButtons: Story = {
  args: {
    direction: 'vertical',
    spacing: 'md',
    children: (
      <>
        <Text size="md" weight="semibold">
          Actions dans une Stack
        </Text>
        <Button variant="primary" size="md">
          Valider
        </Button>
        <Button variant="outline" size="md">
          Annuler
        </Button>
      </>
    ),
  },
}
