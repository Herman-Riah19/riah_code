import type { Meta, StoryObj } from '@storybook/react'
import { Footer } from './Footer'

const meta: Meta<typeof Footer> = {
  title: 'Organisms/Footer',
  component: Footer,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
  args: {
    brand: 'Riah Code',
    tagline: 'La plateforme dentrainement et dinference pour vos modeles de langage.',
    columns: [
      {
        id: 'produit',
        title: 'Produit',
        links: [
          { label: 'Fonctionnalites', href: '#features' },
          { label: 'Tarifs', href: '#pricing' },
          { label: 'Changelog', href: '#changelog' },
        ],
      },
      {
        id: 'ressources',
        title: 'Ressources',
        links: [
          { label: 'Documentation', href: '#docs' },
          { label: 'Guide API', href: '#api' },
          { label: 'Blog', href: '#blog' },
        ],
      },
      {
        id: 'entreprise',
        title: 'Entreprise',
        links: [
          { label: 'A propos', href: '#about' },
          { label: 'Contact', href: '#contact' },
          { label: 'Mentions legales', href: '#legal' },
        ],
      },
    ],
    socialLinks: [
      { label: 'GitHub', href: 'https://github.com' },
      { label: 'X', href: 'https://x.com' },
      { label: 'Discord', href: 'https://discord.com' },
    ],
  },
}

export default meta
type Story = StoryObj<typeof Footer>

export const Default: Story = {}

export const Minimal: Story = {
  args: {
    columns: [],
    socialLinks: [],
    tagline: undefined,
  },
}

export const SingleColumn: Story = {
  args: {
    columns: [
      {
        id: 'liens',
        title: 'Liens utiles',
        links: [
          { label: 'Accueil', href: '#' },
          { label: 'Documentation', href: '#docs' },
        ],
      },
    ],
    socialLinks: [],
  },
}

export const CustomCopyright: Story = {
  args: {
    copyright: '© 2026 Riah Code — Construit avec le design system interne.',
  },
}
