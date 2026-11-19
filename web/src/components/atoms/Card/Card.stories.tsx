import type { Meta, StoryObj } from '@storybook/react'
import { Card } from './Card'
import { Box } from '../Box/Box'
import { Text } from '../Text/Text'
import { Heading } from '../Heading/Heading'

const meta: Meta<typeof Card> = {
  title: 'Atoms/Card',
  component: Card,
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
type Story = StoryObj<typeof Card>

export const Default: Story = {
  args: {
    children: (
      <Box padding="md">
        <Heading level={3} size="lg" weight="semibold" color="default">
          Titre de la carte
        </Heading>
        <Text size="md" color="muted">
          Ceci est une carte par défaut avec un contenu simple.
        </Text>
      </Box>
    ),
  },
}

export const WithFooter: Story = {
  args: {
    children: (
      <>
        <Box padding="md">
          <Heading level={3} size="lg" weight="semibold" color="default">
            Carte avec pied de page
          </Heading>
          <Text size="md" color="muted">
            Contenu principal de la carte.
          </Text>
        </Box>
        <Box padding="md">
          <Text size="sm" color="muted">
            Pied de carte
          </Text>
        </Box>
      </>
    ),
  },
}

export const Interactive: Story = {
  args: {
    children: (
      <Box padding="md">
        <Heading level={3} size="lg" weight="semibold" color="accent">
          Carte interactive
        </Heading>
        <Text size="md" color="muted">
          Contenu de la carte interactive.
        </Text>
      </Box>
    ),
  },
}
