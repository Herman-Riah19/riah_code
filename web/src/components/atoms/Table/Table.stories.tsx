import type { Meta, StoryObj } from '@storybook/react'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableCaption,
} from './Table'

const meta: Meta<typeof Table> = {
  title: 'Atoms/Table',
  component: Table,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    className: {
      control: 'text',
      description: 'Classes CSS additionnelles',
    },
  },
}

export default meta
type Story = StoryObj<typeof Table>

export const Default: Story = {
  args: {
    children: (
      <>
        <TableCaption>Utilisateurs</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>Nom</TableHead>
            <TableHead>Rôle</TableHead>
            <TableHead>Statut</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Alice Dupont</TableCell>
            <TableCell>Administrateur</TableCell>
            <TableCell>Actif</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Bob Martin</TableCell>
            <TableCell>Utilisateur</TableCell>
            <TableCell>Inactif</TableCell>
          </TableRow>
        </TableBody>
      </>
    ),
  },
}
