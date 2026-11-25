import type { Meta, StoryObj } from '@storybook/react'
import { Textfield } from './Textfield'
import { Input } from '@/components/atoms/Input'

const meta: Meta<typeof Textfield> = {
  title: 'Molecules/Textfield',
  component: Textfield,
  parameters: { layout: 'padded' },
  tags: ['autodocs'],
  argTypes: {
    label: { control: 'text', description: 'Libelle du champ' },
    helperText: { control: 'text', description: 'Texte d aide affiche sous le controle' },
    error: { control: 'text', description: 'Message d erreur affiche en rouge' },
  },
  args: {
    label: 'Taille du vocabulaire',
  },
}

export default meta
type Story = StoryObj<typeof Textfield>

export const Default: Story = {
  args: {
    children: <Input type="number" value={32000} min={256} max={200000} />,
  },
}

export const WithHelperText: Story = {
  args: {
    label: 'Echantillon du corpus',
    helperText: 'Nombre de documents utilises pour l entrainement',
    children: <Input type="number" value={20000} min={1} max={1000000} />,
  },
}

export const WithError: Story = {
  args: {
    label: 'Adresse e-mail',
    error: 'Cette adresse e-mail est invalide.',
    children: <Input placeholder="vous@example.com" />,
  },
}

export const Disabled: Story = {
  args: {
    label: 'Threads',
    children: <Input type="number" value={4} min={1} max={64} disabled />,
  },
}
