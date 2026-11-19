import type { StorybookConfig } from '@storybook/react-vite'

const config: StorybookConfig = {
  stories: ['../src/**/*.stories.@(js|jsx|mjs|ts|tsx)'],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
  ],
  framework: {
    name: '@storybook/react-vite',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
  // Désactive le type checking strict de Storybook pour éviter les problèmes
  // de parsing avec TypeScript 6 (verbatimModuleSyntax / erasableSyntaxOnly)
  // qui peuvent générer du JS invalide (Invalid or unexpected token).
  typescript: {
    check: false,
    reactDocgen: 'react-docgen',
  },
}

export default config
