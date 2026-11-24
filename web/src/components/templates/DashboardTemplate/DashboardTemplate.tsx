import type React from 'react'
import { useState } from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Sidebar, type SidebarItem } from '@/components/organisms/Sidebar'
import { Badge } from '@/components/atoms/Badge'
import { Button } from '@/components/atoms/Button'
import { Icon } from '@/components/atoms/Icon'
import { useLocation } from 'react-router-dom'

export interface DashboardTemplateProps {
  sidebarItems?: SidebarItem[]
  activeItem?: string
  brand?: string
  className?: string
  children?: React.ReactNode
}

export const DashboardTemplate: React.FC<DashboardTemplateProps> = ({
  sidebarItems,
  activeItem: propActiveItem,
  brand = 'Riah Code',
  className,
  children,
}) => {
  const { pathname } = useLocation()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const activeItem = propActiveItem ?? (pathname.replace(/^\//, '') || 'dashboard')

  const items: SidebarItem[] = sidebarItems ?? [
    { id: 'corpus', label: 'Corpus', icon: 'database-icon', href: '/corpus' },
    { id: 'tokenizer', label: 'Tokenizer', icon: 'hash-icon', href: '/tokenizer' },
    { id: 'training', label: 'Entrainement', icon: 'play-icon', href: '/training' },
    { id: 'inference', label: 'Inference', icon: 'github-icon', href: '/inference' },
    { id: 'dashboard', label: 'Tableau de bord', icon: 'dashboard-icon', href: '/' },
  ]

  return (
    <Box
      className={[
        'flex min-h-screen bg-background text-foreground',
        className,
      ].filter(Boolean).join(' ')}
    >
      <Sidebar
        items={items}
        activeItem={activeItem}
        brand={brand}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((prev) => !prev)}
        user={{ name: 'Utilisateur', email: 'dev@riah-code.local' }}
      />
      <Box
        as="main"
        className={`flex-1 w-full min-h-screen transition-margin duration-200 ${sidebarCollapsed ? 'ml-16' : 'ml-72'}`}
      >
        <Box
          as="header"
          className="sticky top-0 z-20 flex items-center justify-between px-8 py-6 border-b border-border bg-background/80 backdrop-blur"
        >
          <Stack spacing="xs" className="flex-1 min-w-0">
            <Text size="xs" weight="semibold" color="accent" className="uppercase tracking-wider">
              Riah Code
            </Text>
            <Heading level={1} size="2xl" weight="bold" color="default">
              {activeItem.charAt(0).toUpperCase() + activeItem.slice(1)}
            </Heading>
          </Stack>
          <Box className="flex items-center gap-4">
            <Badge variant="accent" size="sm" dot>
              Systeme en ligne
            </Badge>
            <Button variant="outline" size="sm" onClick={() => {}} aria-label="Notifications">
              <Icon name="bell-icon" size="md" aria-hidden />
            </Button>
            <Box className="flex items-center gap-3 rounded-lg border border-border bg-muted/50 px-3 py-1.5">
              <Box className="h-2 w-2 rounded-full bg-green-500" aria-hidden />
              <Text size="xs" color="default" weight="medium">
                Utilisateur connecte
              </Text>
              <Icon name="chevron-down-icon" size="xs" aria-hidden />
            </Box>
          </Box>
        </Box>
        <Box className="p-8">{children}</Box>
      </Box>
    </Box>
  )
}