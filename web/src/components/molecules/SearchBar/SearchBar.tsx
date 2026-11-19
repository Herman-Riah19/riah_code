import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Input } from '@/components/atoms/Input'
import { Button } from '@/components/atoms/Button'
import { Icon } from '@/components/atoms/Icon'

export interface SearchBarProps {
  placeholder?: string
  value?: string
  onChange?: (value: string) => void
  onSearch?: (value: string) => void
  className?: string
}

export const SearchBar: React.FC<SearchBarProps> = ({
  placeholder,
  value,
  onChange,
  onSearch,
  className,
}) => {
  return (
    <Box
      className={[
        'flex items-center gap-2 rounded-md border border-input bg-background px-3 py-2 focus-within:ring-2 focus-within:ring-ring',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <Icon name="search" size="sm" color="muted" aria-hidden />
      <Input
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange?.(e.currentTarget.value)}
        isFullWidth
        className="bg-transparent border-none focus-visible:ring-0 px-0 text-sm"
      />
      <Button variant="ghost" size="sm" onClick={() => onSearch?.(value ?? '')}>
        Rechercher
      </Button>
    </Box>
  )
}
