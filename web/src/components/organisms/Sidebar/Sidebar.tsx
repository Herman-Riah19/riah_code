import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Text } from '@/components/atoms/Text'
import { Icon } from '@/components/atoms/Icon'
import { Button } from '@/components/atoms/Button'
import { Divider } from '@/components/atoms/Divider'
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

  const itemClasses = (active: boolean) =>
    [
      'w-full flex justify-start rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150',
      'border-transparent',
      active
        ? 'bg-accent/10 border-l-2 border-accent text-accent-foreground'
        : 'text-muted-foreground hover:bg-accent/50 hover:text-accent-foreground',
    ]
      .filter(Boolean)
      .join(' ')

  return (
    <Box
      as="aside"
      className={[
        'fixed left-0 top-0 bottom-0 z-30 flex flex-col shrink-0',
        collapsed ? 'w-16' : 'w-72',
        'bg-card border-r border-border shadow-sm',
        className,
      ].filter(Boolean).join(' ')}
      aria-label="Barre laterale de navigation"
    >
      {/* Brand + toggle */}
      <Box
        as="header"
        className="flex items-center justify-between h-16 px-4 border-b border-border bg-background/50 shrink-0"
      >
        <Box
          onClick={onToggle}
          className="flex items-center gap-3 cursor-pointer hover:bg-accent/5 rounded-lg transition-colors"
          aria-label="Basculer la barre laterale"
        >
          <Box
            className="shrink-0 h-8 w-8 rounded-xl bg-primary text-primary-foreground flex items-center justify-center"
          >
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
          <Icon name="chevron-down-icon" size="md" aria-hidden />
        </Button>
      </Box>

      {/* Navigation */}
      <Box className="flex-1 overflow-y-auto p-3 space-y-1 shrink-0">
        <Stack spacing="xs">
          <Text
            size="xs"
            weight="semibold"
            color="muted"
            className="uppercase tracking-wider px-3 mb-1"
          >
            Navigation
          </Text>
          {items.map((item) => {
            const active = isActive(item)
            return (
              <Button
                key={item.id}
                variant={active ? 'primary' : 'ghost'}
                isFullWidth={!collapsed}
                onClick={() => handleItemClick(item)}
                className={itemClasses(active)}
                aria-pressed={active}
              >
                {!collapsed && (
                  <Text size="sm" weight={active ? 'semibold' : 'medium'} color="default">
                    {item.label}
                  </Text>
                )}
              </Button>
            )
          })}
        </Stack>

        <Divider orientation="horizontal" spacing="sm" variant="subtle" />

        <Stack spacing="xs">
          <Text
            size="xs"
            weight="semibold"
            color="muted"
            className="uppercase tracking-wider px-3 mb-1"
          >
            Rapides
          </Text>
          <Button
            variant="outline"
            isFullWidth={!collapsed}
            onClick={() => navigate('/corpus')}
            className={[
              'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors',
            ].filter(Boolean).join(' ')}
            aria-label="Actualiser les donnees"
          >
            <Box className="shrink-0 h-5 w-5 flex items-center justify-center">
              <Icon name="refresh-cw-icon" size="sm" color="inherit" aria-hidden />
            </Box>
            {!collapsed && <Text size="sm" color="default">Actualiser les donnees</Text>}
          </Button>
        </Stack>
      </Box>

      {/* Footer (utilisateur) */}
      <Box
        as="footer"
        className="h-20 border-t border-border bg-background/50 shrink-0 p-3 flex items-center justify-between"
      >
        <Box
          className={[
            'flex items-center gap-3 min-w-0',
            collapsed ? 'justify-center' : '',
          ].filter(Boolean).join(' ')}
        >
          <Box className="shrink-0 h-9 w-9 rounded-full bg-muted/50 flex items-center justify-center">
            <Text size="xs" weight="bold" color="muted" className="text-center">
              {initials}
            </Text>
          </Box>
          {!collapsed && (
            <Stack spacing="none" className="min-w-0">
              <Text size="sm" weight="semibold" color="default" className="truncate leading-none">
                {userName}
              </Text>
              <Text size="xs" color="muted" className="truncate leading-none">
                {userEmail}
              </Text>
            </Stack>
          )}
        </Box>
        <Box className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="xs"
            className="p-1.5"
            aria-label="Parametres"
          >
            <Icon name="settings-icon" size="sm" aria-hidden />
          </Button>
          <Button
            variant="ghost"
            size="xs"
            className="p-1.5"
            aria-label="Deconnexion"
          >
            <Icon name="user-icon" size="sm" aria-hidden />
          </Button>
        </Box>
      </Box>
    </Box>
  )
}
