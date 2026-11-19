import type { Meta, StoryObj } from '@storybook/react'
import { Flex } from './Flex'
import { Box } from '../Box/Box'
import { Text } from '../Text/Text'
import { Badge } from '../Badge/Badge'

const meta: Meta<typeof Flex> = {
  title: 'Atoms/Flex',
  component: Flex,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    direction: {
      control: 'select',
      options: ['row', 'column', 'row-reverse', 'column-reverse'],
      description: 'Direction de l’axe principal',
    },
    align: {
      control: 'select',
      options: ['start', 'center', 'end', 'stretch', 'baseline'],
      description: 'Alignement sur l’axe transversal',
    },
    justify: {
      control: 'select',
      options: ['start', 'center', 'end', 'between', 'around', 'evenly'],
      description: 'Répartition sur l’axe principal',
    },
    wrap: {
      control: 'boolean',
      description: 'Permet le retour à la ligne',
    },
    gap: {
      control: 'select',
      options: ['none', 'xs', 'sm', 'md', 'lg', 'xl'],
      description: 'Espacement entre les enfants',
    },
    inline: {
      control: 'boolean',
      description: 'Affichage en ligne (inline-flex)',
    },
  },
}

export default meta
type Story = StoryObj<typeof Flex>

export const Default: Story = {
  args: {
    direction: 'row',
    align: 'start',
    justify: 'start',
    wrap: false,
    gap: 'none',
    inline: false,
    children: (
      <>
        <Box padding="xs" borderRadius="sm" border="subtle" background="default">
          <Text size="xs" weight="medium">A</Text>
        </Box>
        <Box padding="xs" borderRadius="sm" border="subtle" background="default">
          <Text size="xs" weight="medium">B</Text>
        </Box>
        <Box padding="xs" borderRadius="sm" border="subtle" background="default">
          <Text size="xs" weight="medium">C</Text>
        </Box>
      </>
    ),
  },
}

export const Centered: Story = {
  args: {
    direction: 'row',
    align: 'center',
    justify: 'center',
    gap: 'md',
    children: (
      <>
        <Box padding="sm" borderRadius="md" border="subtle" background="muted">
          <Text size="sm" weight="medium">Centré</Text>
        </Box>
        <Box padding="sm" borderRadius="md" border="subtle" background="muted">
          <Text size="sm" weight="medium">Aligné centre</Text>
        </Box>
      </>
    ),
  },
}

export const SpaceBetween: Story = {
  args: {
    direction: 'row',
    align: 'center',
    justify: 'between',
    gap: 'md',
    children: (
      <>
        <Box padding="sm" borderRadius="md" border="subtle" background="default">
          <Text size="sm" weight="medium">Début</Text>
        </Box>
        <Box padding="sm" borderRadius="md" border="subtle" background="default">
          <Text size="sm" weight="medium">Fin</Text>
        </Box>
      </>
    ),
  },
}

export const Column: Story = {
  args: {
    direction: 'column',
    align: 'start',
    justify: 'start',
    gap: 'sm',
    children: (
      <>
        <Box padding="xs" borderRadius="sm" border="subtle" background="default">
          <Text size="xs" weight="medium">Ligne 1</Text>
        </Box>
        <Box padding="xs" borderRadius="sm" border="subtle" background="default">
          <Text size="xs" weight="medium">Ligne 2</Text>
        </Box>
        <Box padding="xs" borderRadius="sm" border="subtle" background="default">
          <Text size="xs" weight="medium">Ligne 3</Text>
        </Box>
      </>
    ),
  },
}

export const WithWrap: Story = {
  args: {
    direction: 'row',
    align: 'start',
    justify: 'start',
    wrap: true,
    gap: 'sm',
    children: (
      <>
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Box key={i} padding="xs" borderRadius="sm" border="subtle" background="default">
            <Text size="xs" weight="medium">Élément {i}</Text>
          </Box>
        ))}
      </>
    ),
  },
}

export const WithBadges: Story = {
  args: {
    direction: 'row',
    align: 'center',
    justify: 'start',
    gap: 'sm',
    children: (
      <>
        <Badge variant="success" size="sm">
          Actif
        </Badge>
        <Badge variant="warning" size="sm">
          En attente
        </Badge>
        <Badge variant="error" size="sm">
          Erreur
        </Badge>
      </>
    ),
  },
}
