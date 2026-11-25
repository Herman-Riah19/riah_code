import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Text } from '@/components/atoms/Text'

export interface StatTileProps {
  label: string
  value: string | number
  hint?: string
  /** Taille du texte de la valeur (xs | sm | md | lg | xl) */
  valueSize?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  className?: string
}

/**
 * Tuile de metrique : un libelle en mute au-dessus, une valeur en gras/mono.
 * Utilise dans les panneaux d'information et de preview pour afficher
 * des indicateurscles (vocabulaire, compression, OOV, tokens, etc.).
 */
export const StatTile: React.FC<StatTileProps> = ({
  label,
  value,
  hint,
  valueSize = 'lg',
  className,
}) => (
  <Box
    className={[
      'flex flex-col gap-1 rounded-lg bg-muted/50 p-3',
      className,
    ]
      .filter(Boolean)
      .join(' ')}
  >
    <Text size="xs" color="muted">
      {label}
    </Text>
    <Text size={valueSize} weight="bold" color="default" className="font-mono">
      {value}
    </Text>
    {hint && <Text size="xs" color="muted">{hint}</Text>}
  </Box>
)
