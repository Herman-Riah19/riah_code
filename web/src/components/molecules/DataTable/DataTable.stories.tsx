import type { Meta, StoryObj } from '@storybook/react'
import { DataTable } from './DataTable'

const meta: Meta<typeof DataTable> = {
  title: 'Molecules/DataTable',
  component: DataTable,
  parameters: { layout: 'padded' },
  tags: ['autodocs'],
  argTypes: {
    isLoading: { control: 'boolean' },
    pageSize: { control: 'number' },
  },
}

export default meta
type Story = StoryObj<typeof DataTable>

const columns = [
  { key: 'name', label: 'Nom', sortable: true },
  { key: 'source', label: 'Source', sortable: true },
  { key: 'status', label: 'Statut', sortable: true },
  { key: 'value', label: 'Valeur', align: 'right' as const },
]

const data = [
  { id: 1, name: 'Le petit chat', source: 'wikipedia', status: 'actif', value: 12450 },
  { id: 2, name: 'La Bible', source: 'bible', status: 'actif', value: 8930 },
  { id: 3, name: 'Corpus anglais', source: 'wikipedia', status: 'inactif', value: 6720 },
  { id: 4, name: 'Tokens speciaux', source: 'system', status: 'actif', value: 5210 },
  { id: 5, name: 'Shard 1', source: 'bible', status: 'actif', value: 4890 },
  { id: 6, name: 'Shard 2', source: 'wikipedia', status: 'actif', value: 15320 },
  { id: 7, name: 'Vocabulaire', source: 'system', status: 'actif', value: 3100 },
  { id: 8, name: 'Entrainement', source: 'wikipedia', status: 'en cours', value: 21050 },
]

export const Default: Story = {
  args: { columns, data },
}

export const WithEmpty: Story = {
  args: { columns, data: [], emptyMessage: 'Aucune ligne disponible' },
}

export const Loading: Story = {
  args: { columns, data: [], isLoading: true },
}

export const SmallPage: Story = {
  args: { columns, data, pageSize: 3 },
}
