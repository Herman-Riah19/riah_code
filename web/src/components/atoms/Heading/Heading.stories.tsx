import type { Meta, StoryObj } from '@storybook/react'
import { Heading } from './Heading'

const meta: Meta<typeof Heading> = {
  title: 'Atoms/Heading',
  component: Heading,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    level: {
      control: 'select',
      options: [1, 2, 3, 4, 5, 6],
      description: 'Niveau de titre (h1 à h6)',
    },
    size: {
      control: 'select',
      options: ['xs', 'sm', 'md', 'lg', 'xl', '2xl', '3xl'],
      description: 'Taille visuelle du titre',
    },
    weight: {
      control: 'select',
      options: ['normal', 'medium', 'semibold', 'bold'],
      description: 'Épaisseur de la police',
    },
    color: {
      control: 'select',
      options: ['default', 'muted', 'accent'],
      description: 'Couleur du titre',
    },
  },
}

export default meta
type Story = StoryObj<typeof Heading>

export const Default: Story = {
  args: {
    level: 2,
    size: 'xl',
    weight: 'semibold',
    color: 'default',
    children: 'Titre de niveau 2 par défaut',
  },
}

export const Level1: Story = {
  args: {
    level: 1,
    size: '3xl',
    weight: 'bold',
    color: 'default',
    children: 'Titre principal (h1)',
  },
}

export const Level3: Story = {
  args: {
    level: 3,
    size: 'xl',
    weight: 'semibold',
    color: 'default',
    children: 'Sous-titre (h3)',
  },
}

export const Level6: Story = {
  args: {
    level: 6,
    size: 'sm',
    weight: 'normal',
    color: 'muted',
    children: 'Titre secondaire (h6)',
  },
}

export const Sizes: Story = {
  args: {
    level: 3,
    size: '2xl',
    weight: 'bold',
    color: 'default',
    children: 'Taille 2xl par défaut',
  },
}

export const MutedColor: Story = {
  args: {
    level: 4,
    size: 'lg',
    weight: 'semibold',
    color: 'muted',
    children: 'Titre de couleur muted',
  },
}

export const AccentColor: Story = {
  args: {
    level: 2,
    size: 'xl',
    weight: 'semibold',
    color: 'accent',
    children: 'Titre de couleur accent',
  },
}
