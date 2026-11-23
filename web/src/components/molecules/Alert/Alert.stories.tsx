import type { Meta, StoryObj } from '@storybook/react'
import { Alert } from './Alert'

const meta: Meta<typeof Alert> = {
  title: 'Molecules/Alert',
  component: Alert,
  parameters: { layout: 'centered' },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['info', 'success', 'warning', 'error'],
      description: 'Variante visuelle de l\'alerte',
    },
  },
}

export default meta
type Story = StoryObj<typeof Alert>

export const Info: Story = {
  args: {
    variant: 'info',
    title: 'Information',
    message: 'Ceci est un message d\'information pour l\'utilisateur.',
  },
}

export const Success: Story = {
  args: {
    variant: 'success',
    title: 'Succes',
    message: 'L\'operation s\'est deroulee avec succes.',
  },
}

export const Warning: Story = {
  args: {
    variant: 'warning',
    title: 'Attention',
    message: 'Cette action pourrait avoir des consequences.',
  },
}

export const Error: Story = {
  args: {
    variant: 'error',
    title: 'Erreur',
    message: 'Une erreur est survenue lors du traitement.',
  },
}

export const WithDismiss: Story = {
  args: {
    variant: 'info',
    title: 'Notification',
    message: 'Cette alerte peut etre fermee par l\'utilisateur.',
    onDismiss: () => alert('Fermer!'),
  },
}

export const WithoutTitle: Story = {
  args: {
    variant: 'warning',
    message: 'Message simple sans titre.',
  },
}