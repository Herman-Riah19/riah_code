import type { Meta, StoryObj } from '@storybook/react'
import { CallToAction } from './CallToAction'

const meta: Meta<typeof CallToAction> = {
  title: 'Organisms/CallToAction',
  component: CallToAction,
  tags: ['autodocs'],
  args: {
    title: 'Pret a lancer votre premier run ?',
    description:
      'Creez un compte, importez votre corpus et demarrez un entrainement en quelques minutes.',
    primaryAction: { label: 'Commencer gratuitement' },
    secondaryAction: { label: 'Voir une demo', variant: 'outline' },
    note: 'Sans carte bancaire — annulable a tout moment.',
  },
}

export default meta
type Story = StoryObj<typeof CallToAction>

export const Default: Story = {}

export const SingleAction: Story = {
  args: {
    secondaryAction: undefined,
    note: undefined,
  },
}

export const Minimal: Story = {
  args: {
    description: undefined,
    primaryAction: { label: 'Demarrer' },
    secondaryAction: undefined,
    note: undefined,
  },
}
