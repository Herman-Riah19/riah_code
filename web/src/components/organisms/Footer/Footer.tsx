import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Flex } from '@/components/atoms/Flex'
import { Stack } from '@/components/atoms/Stack'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Divider } from '@/components/atoms/Divider'
import { Icon } from '@/components/atoms/Icon'

export interface FooterLink {
  label: string
  href?: string
}

export interface FooterColumn {
  id: string
  title: string
  links: FooterLink[]
}

export interface FooterProps {
  brand?: string
  tagline?: string
  columns?: FooterColumn[]
  socialLinks?: FooterLink[]
  copyright?: string
  className?: string
}

export const Footer: React.FC<FooterProps> = ({
  brand = 'Riah Code',
  tagline = 'La plateforme d’entrainement et d’inference pour vos modeles de langage.',
  columns = [],
  socialLinks = [],
  copyright,
  className,
}) => {
  const year = new Date().getFullYear()

  return (
    <Box
      as="footer"
      className={['border-t border-border bg-muted/40', className].filter(Boolean).join(' ')}
    >
      <Box className="mx-auto w-full max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <Flex direction="column" gap="lg" className="md:flex-row md:justify-between">
          <Stack spacing="sm" className="max-w-xs">
            <Flex align="center" gap="sm">
              <Flex
                align="center"
                justify="center"
                className="h-8 w-8 rounded-lg bg-primary text-primary-foreground"
              >
                <Icon name="social-icon" size="sm" color="inherit" aria-hidden />
              </Flex>
              <Text as="span" weight="bold" size="lg" color="default">
                {brand}
              </Text>
            </Flex>
            <Text size="sm" color="muted">
              {tagline}
            </Text>
          </Stack>

          <Flex gap="xl" wrap className="flex-wrap gap-8">
            {columns.map((column) => (
              <Stack key={column.id} spacing="sm">
                <Heading level={3} size="sm" weight="semibold" color="default">
                  {column.title}
                </Heading>
                <Stack spacing="xs">
                  {column.links.map((link) => (
                    <Text
                      key={link.label}
                      as="a"
                      href={link.href ?? '#'}
                      size="sm"
                      color="muted"
                      className="transition-colors hover:text-foreground"
                    >
                      {link.label}
                    </Text>
                  ))}
                </Stack>
              </Stack>
            ))}
          </Flex>
        </Flex>

        <Divider className="my-8" />

        <Flex align="center" justify="between" gap="md" className="flex-wrap">
          <Text size="xs" color="muted">
            {copyright ?? `© ${year} ${brand}. Tous droits reserves.`}
          </Text>
          {socialLinks.length > 0 && (
            <Flex align="center" gap="sm">
              {socialLinks.map((link) => (
                <Text
                  key={link.label}
                  as="a"
                  href={link.href ?? '#'}
                  size="xs"
                  color="muted"
                  aria-label={link.label}
                  className="transition-colors hover:text-foreground"
                >
                  {link.label}
                </Text>
              ))}
            </Flex>
          )}
        </Flex>
      </Box>
    </Box>
  )
}
