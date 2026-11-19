import type { Meta, StoryObj } from '@storybook/react'
import { Textarea } from './Textarea'
import { Text } from '../Text/Text'

const meta: Meta<typeof Textarea> = {
  title: 'Atoms/Textarea',
  component: Textarea,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'error', 'success'],
      description: 'État de validation',
    },
    resize: {
      control: 'select',
      options: ['none', 'vertical', 'horizontal', 'both'],
      description: 'Redimensionnement autorisé',
    },
    isFullWidth: {
      control: 'boolean',
      description: 'Champ sur toute la largeur',
    },
    disabled: {
      control: 'boolean',
      description: 'Champ désactivé',
    },
    readOnly: {
      control: 'boolean',
      description: 'Champ en lecture seule',
    },
    minRows: {
      control: 'number',
      description: 'Nombre minimal de lignes',
    },
    placeholder: {
      control: 'text',
      description: 'Texte d’espace réservé',
    },
  },
}

export default meta
type Story = StoryObj<typeof Textarea>

export const Default: Story = {
  args: {
    variant: 'default',
    resize: 'vertical',
    isFullWidth: false,
    minRows: 3,
    placeholder: 'Écrivez votre message ici…',
  },
}

export const Variants: Story = {
  args: {
    variant: 'error',
    resize: 'vertical',
    minRows: 3,
    placeholder: 'Champ en erreur',
  },
}

export const Success: Story = {
  args: {
    variant: 'success',
    resize: 'vertical',
    minRows: 3,
    placeholder: 'Champ validé',
  },
}

export const NoResize: Story = {
  args: {
    variant: 'default',
    resize: 'none',
    minRows: 4,
    placeholder: 'Sans redimensionnement',
  },
}

export const BothResize: Story = {
  args: {
    variant: 'default',
    resize: 'both',
    minRows: 3,
    placeholder: 'Redimensionnable dans les deux sens',
  },
}

export const FullWidth: Story = {
  args: {
    variant: 'default',
    resize: 'vertical',
    isFullWidth: true,
    minRows: 4,
    placeholder: 'Champ sur toute la largeur',
  },
}

export const Disabled: Story = {
  args: {
    variant: 'default',
    resize: 'vertical',
    minRows: 3,
    placeholder: 'Champ désactivé',
    disabled: true,
  },
}

export const ReadOnly: Story = {
  args: {
    variant: 'default',
    resize: 'vertical',
    minRows: 3,
    placeholder: 'Lecture seule',
    readOnly: true,
    defaultValue: 'Contenu en lecture seule…',
  },
}

export const WithLabel: Story = {
  args: {
    variant: 'default',
    resize: 'vertical',
    minRows: 4,
    placeholder: 'Décrivez votre besoin…',
    children: (
      <Text size="sm" weight="medium" color="emphasis" as="label" htmlFor="message-input">
        Message
      </Text>
    ),
  },
}
