import type { Meta, StoryObj } from '@storybook/react'
import { Box } from './Box'
import { Text } from '../Text/Text'
import { Heading } from '../Heading/Heading'

const meta: Meta<typeof Box> = {
  title: 'Atoms/Box',
  component: Box,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    as: {
      control: 'select',
      options: ['div', 'section', 'article', 'main', 'header', 'footer'],
      description: 'Balise HTML rendue sous-jacente',
    },
    padding: {
      control: 'select',
      options: ['none', 'xs', 'sm', 'md', 'lg', 'xl', '2xl'],
      description: 'Rembourrage intérieur',
    },
    paddingX: {
      control: 'select',
      options: ['none', 'xs', 'sm', 'md', 'lg', 'xl', '2xl'],
      description: 'Rembourrage horizontal',
    },
    paddingY: {
      control: 'select',
      options: ['none', 'xs', 'sm', 'md', 'lg', 'xl', '2xl'],
      description: 'Rembourrage vertical',
    },
    margin: {
      control: 'select',
      options: ['none', 'xs', 'sm', 'md', 'lg', 'xl', '2xl'],
      description: 'Marge extérieure',
    },
    borderRadius: {
      control: 'select',
      options: ['none', 'sm', 'md', 'lg', 'xl', 'full'],
      description: 'Arrondi des coins',
    },
    border: {
      control: 'select',
      options: ['none', 'subtle', 'default', 'accent'],
      description: 'Style de bordure',
    },
    background: {
      control: 'select',
      options: ['transparent', 'default', 'muted', 'accent'],
      description: 'Couleur de fond',
    },
  },
}

export default meta
type Story = StoryObj<typeof Box>

export const Default: Story = {
  args: {
    padding: 'md',
    borderRadius: 'md',
    border: 'subtle',
    children: 'Box par défaut avec rembourrage md et bordure subtle',
  },
}

export const PaddingVariants: Story = {
  args: {
    padding: 'lg',
    borderRadius: 'lg',
    border: 'default',
    children: (
      <>
        <Heading level={2} size="lg" color="accent">
          Variantes de padding
        </Heading>
        <Text size="md" color="muted">
          Ce Box utilise un padding lg et un border-radius lg.
        </Text>
      </>
    ),
  },
}

export const BackgroundVariants: Story = {
  args: {
    padding: 'md',
    borderRadius: 'md',
    background: 'muted',
    children: 'Box avec fond muted',
  },
}

export const AccentBox: Story = {
  args: {
    padding: 'md',
    borderRadius: 'md',
    border: 'accent',
    background: 'accent',
    children: 'Box avec bordure et fond accent',
  },
}

export const FullRoundBox: Story = {
  args: {
    padding: 'md',
    borderRadius: 'full',
    border: 'subtle',
    background: 'default',
    children: 'Box aux bords entièrement arrondis (full)',
  },
}

export const PolymorphicSection: Story = {
  args: {
    as: 'section',
    padding: 'lg',
    borderRadius: 'xl',
    border: 'default',
    children: (
      <>
        <Heading level={2} size="xl">Une section sémantique</Heading>
        <Text size="sm" color="muted">
          Ce Box rend une balise &lt;section&gt; via la prop as.
        </Text>
      </>
    ),
  },
}
