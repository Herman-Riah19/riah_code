import type React from 'react'
import {
  AlertCircle,
  ArrowRight,
  Bell,
  BookOpen,
  Calendar,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CircleCheck,
  CircleX,
  Clock,
  Cloud,
  Code,
  CreditCard,
  Database,
  Download,
  ExternalLink,
  FileText,
  Globe,
  HardDrive,
  LayoutDashboard,
  LoaderCircle,
  MessageCircle,
  Play,
  RefreshCw,
  RotateCw,
  Search,
  Settings,
  Sparkles,
  Square,
  Sun,
  Moon,
  User,
  X,
  type LucideIcon,
} from 'lucide-react'

export type IconSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'
export type IconColor =
  | 'default'
  | 'muted'
  | 'accent'
  | 'error'
  | 'success'
  | 'warning'
  | 'inherit'

export interface IconProps {
  name: string
  size?: IconSize
  color?: IconColor
  className?: string
  style?: React.CSSProperties
  'aria-label'?: string
  'aria-hidden'?: boolean | 'true' | 'false'
}

const SIZE_MAP: Record<IconSize, string> = {
  xs: 'h-3 w-3',
  sm: 'h-4 w-4',
  md: 'h-5 w-5',
  lg: 'h-6 w-6',
  xl: 'h-8 w-8',
}

const SIZE_PIXELS: Record<IconSize, number> = {
  xs: 12,
  sm: 16,
  md: 20,
  lg: 24,
  xl: 32,
}

const COLOR_MAP: Record<IconColor, string> = {
  default: 'text-foreground',
  muted: 'text-muted-foreground',
  accent: 'text-accent-foreground',
  error: 'text-destructive',
  success: 'text-green-600',
  warning: 'text-yellow-600',
  inherit: '',
}

/**
 * Map legacy sprite names (and a few lucide aliases) to lucide components.
 * This keeps every existing `<Icon name="..." />` call working.
 */
const ICON_MAP: Record<string, LucideIcon> = {
  alert: AlertCircle,
  'alert-circle-icon': AlertCircle,
  'arrow-right': ArrowRight,
  'bell-icon': Bell,
  'bluesky-icon': Cloud,
  'calendar-icon': Calendar,
  check: Check,
  'check-circle-icon': CircleCheck,
  'check-icon': Check,
  'chevron-down-icon': ChevronDown,
  'chevron-left-icon': ChevronLeft,
  'chevron-right-icon': ChevronRight,
  'clock-icon': Clock,
  'credit-card-icon': CreditCard,
  'dashboard-icon': LayoutDashboard,
  'database-icon': Database,
  'discord-icon': MessageCircle,
  'documentation-icon': BookOpen,
  'download-icon': Download,
  'external-link-icon': ExternalLink,
  'file-text-icon': FileText,
  'github-icon': Code,
  'globe-icon': Globe,
  'hard-drive-icon': HardDrive,
  'loader-icon': LoaderCircle,
  'moon-icon': Moon,
  'play-icon': Play,
  'refresh-cw-icon': RefreshCw,
  'rotate-cw-icon': RotateCw,
  search: Search,
  settings: Settings,
  'settings-icon': Settings,
  'social-icon': Sparkles,
  'square-icon': Square,
  'sun-icon': Sun,
  'user-icon': User,
  'x-circle-icon': CircleX,
  'x-icon': X,
}

export const Icon: React.FC<IconProps> = ({
  name,
  size = 'md',
  color = 'inherit',
  className = '',
  style,
  'aria-label': ariaLabel,
  'aria-hidden': ariaHidden,
}) => {
  const LucideComponent = ICON_MAP[name] ?? Square
  const cls = [SIZE_MAP[size], COLOR_MAP[color], className].filter(Boolean).join(' ')

  return (
    <LucideComponent
      className={cls}
      size={SIZE_PIXELS[size]}
      strokeWidth={2}
      style={style}
      role={ariaLabel ? 'img' : 'presentation'}
      aria-label={ariaLabel}
      aria-hidden={ariaLabel ? undefined : (ariaHidden ?? true)}
    />
  )
}
