import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Text } from '@/components/atoms/Text'
import { Icon } from '@/components/atoms/Icon'
import { Button } from '@/components/atoms/Button'
import { Divider } from '@/components/atoms/Divider'
import { ThemeToggle } from '@/components/molecules/ThemeToggle'
import { useLocation, useNavigate } from 'react-router-dom'

export interface SidebarItem {
  id: string
  label: string
  icon?: string
  href?: string
}

export interface SidebarUser {
  name?: string
  email?: string
}

export interface SidebarProps {
  items: SidebarItem[]
  activeItem?: string
  brand?: string
  className?: string
  collapsed?: boolean
  onToggle?: () => void
  user?: SidebarUser
}

const FOCUS_RING =
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring focus-visible:ring-offset-2'

export const Sidebar: React.FC<SidebarProps> = ({
  items = [],
  activeItem,
  brand = 'Riah Code',
  className,
  collapsed = false,
  onToggle,
  user,
}) => {
  const navigate = useNavigate()
  const { pathname } = useLocation()

  const handleItemClick = (item: SidebarItem) => {
    if (item.href) {
      navigate(item.href)
    }
  }

  const isActive = (item: SidebarItem) => {
    if (activeItem && item.id === activeItem) return true
    if (item.href && pathname === item.href) return true
    return false
  }

  const userName = user?.name || 'Utilisateur'
  const userEmail = user?.email || 'dev@riah-code.local'
  const initials = (user?.name || 'U')
    .split(' ')
    .map((part) => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  return (
    <Box
      as="aside"
      className={[
        'fixed left-0 top-0 bottom-0 z-30 flex flex-col shrink-0',
        collapsed ? 'w-16' : 'w-72',
        'bg-sidebar border-r border-sidebar-border shadow-sm',
        className,
      ].filter(Boolean).join(' ')}
      aria-label="Barre laterale de navigation"
    >
      {/* Brand + toggle */}
      <Box
        as="header"
        className="flex items-center justify-between h-16 px-4 border-b border-sidebar-border bg-sidebar/80 shrink-0"
      >
        <Box
          as="button"
          onClick={onToggle}
          aria-label="Basculer la barre laterale"
          className={[
            'flex items-center gap-3 rounded-lg text-left transition-colors hover:bg-sidebar-primary/10',
            FOCUS_RING,
          ].join(' ')}
        >
          <Box className="flex-shrink-0 h-8 w-8 rounded-xl bg-sidebar-primary text-sidebar-primary-foreground flex items-center justify-center">
            <Icon name="social-icon" size="md" color="inherit" aria-hidden />
          </Box>
          {!collapsed && (
            <Text size="sm" weight="bold" color="default" className="tracking-tight truncate">
              {brand}
            </Text>
          )}
        </Box>
        <Button
          variant="ghost"
          size="xs"
          onClick={onToggle}
          className="ml-auto"
          aria-label={collapsed ? 'Etendre la barre laterale' : 'Reduire la barre laterale'}
        >
          <Icon name={collapsed ? 'chevron-right-icon' : 'chevron-left-icon'} size="md" aria-hidden />
        </Button>
      </Box>

      {/* Navigation */}
      <Box className="flex-1 overflow-y-auto p-3 space-y-1 shrink-0">
        <Stack spacing="xs">
          {!collapsed && (
            <Text
              size="xs"
              weight="semibold"
              color="muted"
              className="uppercase tracking-wider px-3 mb-1"
            >
              Navigation
            </Text>
          )}
          {items.map((item) => {
            const active = isActive(item)
            return (
              <Box
                as="button"
                key={item.id}
                onClick={() => handleItemClick(item)}
                aria-pressed={active}
                className={[
                  'flex w-full items-center rounded-lg py-2.5 text-sm font-medium transition-all duration-150',
                  collapsed ? 'justify-center px-2' : 'gap-3 px-3',
                  active
                    ? 'bg-sidebar-primary/10 border-l-2 border-sidebar-primary text-sidebar-foreground'
                    : 'border-l-2 border-transparent text-muted-foreground hover:bg-sidebar-primary/10 hover:text-sidebar-foreground',
                  FOCUS_RING,
                ]
                  .filter(Boolean)
                  .join(' ')}
              >
                <Box className="flex-shrink-0 h-5 w-5 flex items-center justify-center">
                  <Icon
                    name={item.icon || 'dashboard-icon'}
                    size="sm"
                    color="inherit"
                    aria-hidden
                  />
                </Box>
                {!collapsed && (
                  <Text
                    size="sm"
                    weight={active ? 'semibold' : 'medium'}
                    color="default"
                    className="truncate"
                  >
                    {item.label}
                  </Text>
                )}
                {active && !collapsed && (
                  <Box className="ml-auto h-1.5 w-1.5 flex-shrink-0 rounded-full bg-sidebar-primary" aria-hidden />
                )}
              </Box>
            )
          })}
        </Stack>

        <Divider orientation="horizontal" spacing="sm" variant="subtle" />

        <Stack spacing="xs">
          {!collapsed && (
            <Text
              size="xs"
              weight="semibold"
              color="muted"
              className="uppercase tracking-wider px-3 mb-1"
            >
              Rapides
            </Text>
          )}
          <Box
            as="button"
            onClick={() => navigate('/corpus')}
            aria-label="Actualiser les donnees"
            className={[
              'flex w-full items-center rounded-lg py-2.5 text-sm transition-colors text-muted-foreground hover:bg-sidebar-primary/10 hover:text-sidebar-foreground',
              collapsed ? 'justify-center px-2' : 'gap-3 px-3',
              FOCUS_RING,
            ].join(' ')}
          >
            <Box className="flex-shrink-0 h-5 w-5 flex items-center justify-center">
              <Icon name="refresh-cw-icon" size="sm" color="inherit" aria-hidden />
            </Box>
            {!collapsed && (
              <Text size="sm" color="default" className="truncate">
                Actualiser les donnees
              </Text>
            )}
          </Box>
        </Stack>
      </Box>

      {/* Footer (utilisateur) */}
      <Box
        as="footer"
        className={[
          'border-t border-sidebar-border bg-sidebar/80 shrink-0 p-3 flex',
          collapsed ? 'h-28 flex-col items-center justify-center gap-2' : 'h-20 items-center justify-between',
        ].join(' ')}
      >
        <Box
          className={[
            'flex items-center gap-3 min-w-0',
            collapsed ? 'justify-center' : '',
          ].filter(Boolean).join(' ')}
        >
          <Box className="flex-shrink-0 h-9 w-9 rounded-full bg-muted/50 flex items-center justify-center">
            <Text size="xs" weight="bold" color="muted" className="text-center">
              {initials}
            </Text>
          </Box>
          {!collapsed && (
            <Stack spacing="none" className="min-w-0">
              <Text size="sm" weight="semibold" color="default" className="truncate leading-tight">
                {userName}
              </Text>
              <Text size="xs" color="muted" className="truncate leading-tight">
                {userEmail}
              </Text>
            </Stack>
          )}
        </Box>
        <Box className="flex items-center gap-2">
          <ThemeToggle />
          {!collapsed && (
            <>
              <Button variant="ghost" size="xs" className="p-1.5" aria-label="Parametres">
                <Icon name="settings-icon" size="sm" aria-hidden />
              </Button>
              <Button variant="ghost" size="xs" className="p-1.5" aria-label="Deconnexion">
                <Icon name="user-icon" size="sm" aria-hidden />
              </Button>
            </>
          )}
        </Box>
      </Box>
    </Box>
  )
}
