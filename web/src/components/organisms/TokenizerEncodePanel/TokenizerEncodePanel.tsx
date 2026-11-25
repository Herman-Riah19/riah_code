import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Divider } from '@/components/atoms/Divider'
import { Button } from '@/components/atoms/Button'
import { Input } from '@/components/atoms/Input'
import { Icon } from '@/components/atoms/Icon'
import { Alert } from '@/components/molecules/Alert'
import { ToggleGroup, type ToggleOption } from '@/components/molecules/ToggleGroup'
import { Textfield } from '@/components/molecules/Textfield'
import { formatNumber } from '@/utils/format'

export interface TokenizerEncodePanelProps {
  shardSizeTokens: number
  onShardSizeTokensChange: (value: number) => void
  languages: string[]
  onLanguagesChange: (languages: string[]) => void
  availableLanguages: string[]
  hasTokenizer: boolean
  onEncode: () => void
  isStarting: boolean
  isDisabled?: boolean
  className?: string
}

export const TokenizerEncodePanel: React.FC<TokenizerEncodePanelProps> = ({
  shardSizeTokens,
  onShardSizeTokensChange,
  languages,
  onLanguagesChange,
  availableLanguages,
  hasTokenizer,
  onEncode,
  isStarting,
  isDisabled = false,
  className,
}) => {
  const languageOptions: ToggleOption[] = (
    availableLanguages.length > 0 ? availableLanguages : ['fr', 'en']
  ).map((language) => ({ value: language, label: language.toUpperCase() }))

  const handleShardSizeChange = (raw: string) => {
    const parsed = Number.parseInt(raw, 10)
    if (Number.isNaN(parsed)) return
    onShardSizeTokensChange(Math.min(100_000_000, Math.max(1_000, parsed)))
  }

  return (
    <Box
      className={[
        'rounded-xl border border-border bg-card p-6 shadow-sm',
        className,
      ].filter(Boolean).join(' ')}
    >
      <Stack spacing="md">
        <Stack spacing="sm">
          <Heading level={2} size="lg" weight="semibold" color="default">
            Encoder le corpus
          </Heading>
          <Text size="sm" color="muted">
            Transformez chaque document nettoye en identifiants et ecrivez des shards binaires.
          </Text>
        </Stack>

        <Divider className="mb-2" />

        {!hasTokenizer && (
          <Alert
            variant="warning"
            title="Tokenizer requis"
            message="Entrainez un tokenizer avant de lancer l'encodage du corpus."
          />
        )}

        <Textfield
          label="Taille des shards (tokens)"
          helperText={formatNumber(shardSizeTokens)}
        >
          <Input
            type="number"
            value={shardSizeTokens}
            min={1000}
            max={100000000}
            step={100000}
            disabled={isDisabled}
            onChange={(event) => handleShardSizeChange(event.currentTarget.value)}
          />
        </Textfield>

        <Stack spacing="sm">
          <Flex align="center" justify="between">
            <Text size="sm" weight="semibold" color="default">
              Langues a encoder
            </Text>
            <Text size="xs" color="muted">
              {languages.length === 0 ? 'Toutes les langues' : `${languages.length} selectionnee(s)`}
            </Text>
          </Flex>
          <ToggleGroup
            options={languageOptions}
            value={languages}
            onChange={onLanguagesChange}
            multiple
            isDisabled={isDisabled}
          />
          <Text size="xs" color="muted">
            Laissez vide pour encoder l'integralite du corpus.
          </Text>
        </Stack>

        <Flex align="center" justify="end" className="pt-2">
          <Button
            variant="primary"
            size="lg"
            isLoading={isStarting}
            onClick={onEncode}
            disabled={isDisabled || isStarting || !hasTokenizer}
            leftIcon={!isStarting && <Icon name="download-icon" size="md" aria-hidden />}
          >
            {isStarting ? 'Encodage en cours...' : 'Encoder le corpus'}
          </Button>
        </Flex>
      </Stack>
    </Box>
  )
}
