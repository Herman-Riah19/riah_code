import type React from 'react'
import { Stack } from '@/components/atoms/Stack'
import { Text } from '@/components/atoms/Text'

export interface TextfieldProps {
  /** Libelle affiche au-dessus du controle */
  label?: string
  /** Texte d'aide affiche sous le controle */
  helperText?: string
  /** Message d'erreur affiche en rouge sous le controle */
  error?: string
  children?: React.ReactNode
  className?: string
}

/**
 * Champ de formulaire compose : un libelle optionnel, un controle (Input,
 * Select ou Textarea) passe en enfants, et un texte d'aide ou d'erreur optionnel.
 *
 * Remplace le pattern repetitif :
 *   <Stack spacing="xs">
 *     <Text size="sm" weight="semibold" color="default">{label}</Text>
 *     <Input ... />
 *   </Stack>
 */
export const Textfield: React.FC<TextfieldProps> = ({
  label,
  helperText,
  error,
  children,
  className,
}) => (
  <Stack spacing="xs" className={className}>
    {label && (
      <Text size="sm" weight="semibold" color="default">
        {label}
      </Text>
    )}
    {children}
    {helperText && <Text size="xs" color="muted">{helperText}</Text>}
    {error && <Text size="xs" color="error">{error}</Text>}
  </Stack>
)
