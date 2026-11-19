import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Button } from '@/components/atoms/Button'
import { Badge } from '@/components/atoms/Badge'
import { Icon } from '@/components/atoms/Icon'

export interface NavbarLink {
  label: string
  href?: string
  isActive?: boolean
}

export interface NavbarAction {
  label: string
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  href?: string
}

export interface NavbarProps {
  brand?: string
  brandHref?: string
  links?: NavbarLink[]
  actions?: NavbarAction[]
  badge?: string
  className?: string
}

export const Navbar: React.FC<NavbarProps> = ({
  brand = 'Riah Code',
  brandHref = '#',
  links = [],
  actions = [],
  badge,
  className,
}) => {
  return (
    <Box
      as="header"
      className={[
        'sticky top-0 z-40 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <Flex
        align="center"
        justify="between"
        gap="lg"
        className="mx-auto h-16 w-full max-w-7xl px-4 sm:px-6 lg:px-8"
      >
        <Flex align="center" gap="sm">
          <Text
            as="a"
            href={brandHref}
            className="flex items-center gap-2 text-foreground no-underline"
          >
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
          </Text>
          {badge && (
            <Badge variant="accent" size="sm">
              {badge}
            </Badge>
          )}
        </Flex>

        <Flex as="nav" align="center" gap="md" className="hidden md:flex">
          {links.map((link) => (
            <Text
              key={link.label}
              as="a"
              href={link.href ?? '#'}
              size="sm"
              weight={link.isActive ? 'semibold' : 'normal'}
              color={link.isActive ? 'default' : 'muted'}
              className="transition-colors hover:text-foreground"
            >
              {link.label}
            </Text>
          ))}
        </Flex>

        <Flex align="center" gap="sm">
          {actions.map((action) => (
            <Button key={action.label} variant={action.variant ?? 'outline'} size="sm">
              {action.label}
            </Button>
          ))}
        </Flex>
      </Flex>
    </Box>
  )
}
