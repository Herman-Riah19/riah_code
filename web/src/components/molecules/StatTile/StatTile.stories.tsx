import type { Meta, StoryObj } from '@storybook/react'
import { StatTile } from './StatTile'

const meta: Meta<typeof StatTile> = {
  title: 'Molecules/StatTile',
  component: StatTile,
  parameters: { layout: 'padded' },
  tags: ['autodocs'],
  argTypes: {
    label: { control: 'text', description: 'Libelle de la metrique' },
    value: { control: 'text', description: 'Valeur affichee' },
    hint: { control: 'text', description: 'Indication secondaire affiche sous la valeur' },
  },
}

export default meta
type Story = StoryObj<typeof StatTile>

export const Default: Story = {
  args: {
    label: 'Taille du vocabulaire',
    value: '32 000',
    hint: 'tokens disponibles',
  },
}

export const WithPercentage: Story = {
  args: {
    label: 'Taux OOV',
    value: '0.00 %',
    hint: 'tokens inconnus',
  },
}
