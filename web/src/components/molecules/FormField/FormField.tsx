import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Text } from '@/components/atoms/Text'

export interface FormFieldProps {
  label?: string
  error?: string
  children?: React.ReactNode
  className?: string
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  error,
  children,
  className,
}) => {
  return (
    <Box className={['space-y-1', className].filter(Boolean).join(' ')}>
      {label && <Text size="sm" weight="medium" color="default">{label}</Text>}
      {children}
      {error && <Text size="xs" color="error">{error}</Text>}
    </Box>
  )
}
