import type { Meta, StoryObj } from '@storybook/react'
import { FormField } from './FormField'
import { Input } from '@/components/atoms/Input'

const meta: Meta<typeof FormField> = {
  title: 'Molecules/FormField',
  component: FormField,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    label: {
      control: 'text',
      description: 'Libellé du champ',
    },
    error: {
      control: 'text',
      description: 'Message d’erreur',
    },
  },
}

export default meta
type Story = StoryObj<typeof FormField>

export const Default: Story = {
  args: {
    label: 'Adresse e-mail',
    children: <Input placeholder="vous@example.com" />,
  },
}

export const WithError: Story = {
  args: {
    label: 'Adresse e-mail',
    error: 'Cette adresse e-mail est invalide.',
    children: <Input placeholder="vous@example.com" />,
  },
}
