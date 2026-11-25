import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Badge } from '@/components/atoms/Badge'
import { Divider } from '@/components/atoms/Divider'
import { Icon } from '@/components/atoms/Icon'
import { EmptyState } from '@/components/molecules/EmptyState'
import { StatTile } from '@/components/molecules/StatTile'
import { formatDate, formatNumber } from '@/utils/format'
import type { TokenizerVocabInfo } from '@/types/tokenizer'

export interface TokenizerInfoPanelProps {
  info: TokenizerVocabInfo | null
  isLoading?: boolean
  className?: string
}

export const TokenizerInfoPanel: React.FC<TokenizerInfoPanelProps> = ({
  info,
  isLoading = false,
  className,
}) => {
  return (
    <Box
      className={[
        'rounded-xl border border-border bg-card p-6 shadow-sm',
        className,
      ].filter(Boolean).join(' ')}
    >
      <Stack spacing="md">
        <Flex align="start" justify="between" gap="md" wrap>
          <Flex align="center" gap="sm">
            <Flex
              align="center"
              justify="center"
              className="h-10 w-10 flex-shrink-0 rounded-lg bg-accent/20"
            >
              <Icon name="hash-icon" size="md" color="accent" aria-hidden />
            </Flex>
            <Stack spacing="xs">
              <Flex align="center" gap="sm">
                <Heading level={2} size="lg" weight="semibold" color="default">
                  Tokenizer actif
                </Heading>
                {info && (
                  <Badge variant="success" size="sm" dot>
                    Pret
                  </Badge>
                )}
              </Flex>
              <Text size="sm" color="muted">
                Artefacts persistes dans data/tokenizer/
              </Text>
            </Stack>
          </Flex>
          {info && (
            <Badge variant="default" size="sm">
              {info.configHash}
            </Badge>
          )}
        </Flex>

        <Divider />

        {isLoading && (
          <Text size="sm" color="muted">Chargement des informations du tokenizer...</Text>
        )}

        {!isLoading && !info && (
          <EmptyState
            icon="hash-icon"
            title="Aucun tokenizer entraine"
            description="Lancez un entrainement BPE ci-dessous pour generer tokenizer.json et vocab_info.json."
          />
        )}

        {!isLoading && info && (
          <Stack spacing="md">
            <Box className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <StatTile
                label="Taille du vocabulaire"
                value={formatNumber(info.vocabSize)}
                hint="tokens disponibles"
                valueSize="xl"
              />
              <StatTile
                label="Compression"
                value={info.compressionRatio.toFixed(2)}
                hint="caracteres / token"
                valueSize="xl"
              />
              <StatTile
                label="Taux OOV"
                value={`${(info.oovRate * 100).toFixed(2)} %`}
                hint="tokens inconnus"
                valueSize="xl"
              />
              <StatTile
                label="Tokens speciaux"
                value={Object.keys(info.specialTokenIds).length.toString()}
                hint="reserves au modele"
                valueSize="xl"
              />
            </Box>

            <Flex wrap gap="md" className="rounded-lg border border-border bg-muted/30 p-3">
              <Flex align="center" gap="xs">
                <Icon name="calendar-icon" size="xs" color="muted" aria-hidden />
                <Text size="xs" color="muted">
                  Entraine le{' '}
                  <Text as="span" weight="medium" color="default">
                    {formatDate(info.trainedAt)}
                  </Text>
                </Text>
              </Flex>
              <Flex align="center" gap="xs">
                <Icon name="info-icon" size="xs" color="muted" aria-hidden />
                <Text size="xs" color="muted">
                  Hash config{' '}
                  <Text as="span" weight="medium" color="default" className="font-mono">
                    {info.configHash}
                  </Text>
                </Text>
              </Flex>
            </Flex>

            <Stack spacing="sm">
              <Text size="xs" weight="semibold" color="muted" className="uppercase tracking-wide">
                Tokens speciaux
              </Text>
              <Flex wrap gap="sm">
                {Object.entries(info.specialTokenIds).map(([token, tokenId]) => (
                  <Box
                    key={token}
                    className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-2.5 py-1"
                  >
                    <Text size="sm" mono color="default">{token}</Text>
                    <Badge variant="muted" size="sm">{tokenId}</Badge>
                  </Box>
                ))}
              </Flex>
            </Stack>
          </Stack>
        )}
      </Stack>
    </Box>
  )
}
