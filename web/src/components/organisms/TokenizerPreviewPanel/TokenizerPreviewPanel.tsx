import type React from 'react'
import { useState } from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Badge } from '@/components/atoms/Badge'
import { Divider } from '@/components/atoms/Divider'
import { Button } from '@/components/atoms/Button'
import { Textarea } from '@/components/atoms/Textarea'
import { Icon } from '@/components/atoms/Icon'
import { Alert } from '@/components/molecules/Alert'
import { formatNumber } from '@/utils/format'
import type { TokenPreview } from '@/types/tokenizer'

export interface TokenizerPreviewPanelProps {
  preview: TokenPreview | null
  isPreviewing: boolean
  error: string | null
  onPreview: (text: string) => void
  onClear: () => void
  isDisabled?: boolean
  defaultText?: string
  className?: string
}

/** Make byte-level markers visible in the token chips. */
function displayToken(token: string): string {
  return token
    .replace(/Ġ/g, '␣')
    .replace(/\n/g, '⏎')
    .replace(/\t/g, '⇥')
}

interface PreviewMetricProps {
  label: string
  value: string
}

const PreviewMetric: React.FC<PreviewMetricProps> = ({ label, value }) => (
  <Box className="flex flex-col gap-1 rounded-lg bg-muted/50 p-3">
    <Text size="xs" color="muted">{label}</Text>
    <Text size="lg" weight="bold" color="default" className="font-mono">
      {value}
    </Text>
  </Box>
)

export const TokenizerPreviewPanel: React.FC<TokenizerPreviewPanelProps> = ({
  preview,
  isPreviewing,
  error,
  onPreview,
  onClear,
  isDisabled = false,
  defaultText = '',
  className,
}) => {
  const [text, setText] = useState(defaultText)

  const handlePreview = () => {
    onPreview(text)
  }

  const handleClear = () => {
    setText('')
    onClear()
  }

  return (
    <Box
      className={[
        'rounded-xl border border-border bg-card p-6 shadow-sm',
        className,
      ].filter(Boolean).join(' ')}
    >
      <Stack spacing="md">
        <Flex align="start" justify="between" gap="md" wrap>
          <Stack spacing="sm">
            <Heading level={2} size="lg" weight="semibold" color="default">
              Previsualiser la tokenisation
            </Heading>
            <Text size="sm" color="muted">
              Testez un texte avec le tokenizer actif avant de lancer l encodage complet.
            </Text>
          </Stack>
          <Badge variant="accent" size="sm">Playground</Badge>
        </Flex>

        <Divider className="mb-2" />

        <Stack spacing="xs">
          <Text size="sm" weight="semibold" color="default">
            Texte a analyser
          </Text>
          <Textarea
            value={text}
            onChange={(event) => setText(event.currentTarget.value)}
            placeholder="Saisissez une phrase pour voir comment elle est decoupee en tokens..."
            minRows={4}
            disabled={isDisabled}
          />
        </Stack>

        {error && (
          <Alert
            variant="error"
            title="Previsualisation impossible"
            message={error}
          />
        )}

        <Flex align="center" justify="end" gap="sm">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            disabled={isPreviewing}
            leftIcon={<Icon name="refresh-cw-icon" size="sm" aria-hidden />}
          >
            Reinitialiser
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handlePreview}
            isLoading={isPreviewing}
            disabled={isDisabled || isPreviewing || text.trim().length === 0}
            leftIcon={!isPreviewing && <Icon name="search-icon" size="md" aria-hidden />}
          >
            {isPreviewing ? 'Tokenisation...' : 'Tokenizer le texte'}
          </Button>
        </Flex>

        {preview && (
          <Stack spacing="md">
            <Divider className="my-2" />

            <Box className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <PreviewMetric label="Tokens" value={formatNumber(preview.tokenCount)} />
              <PreviewMetric label="Caracteres" value={formatNumber(preview.characterCount)} />
              <PreviewMetric label="Compression" value={`${preview.compressionRatio.toFixed(2)}`} />
              <PreviewMetric
                label="Dernier ID"
                value={preview.tokenIds.length > 0
                  ? formatNumber(preview.tokenIds[preview.tokenIds.length - 1])
                  : '-'}
              />
            </Box>

            <Stack spacing="sm">
              <Flex align="center" justify="between">
                <Text size="xs" weight="semibold" color="muted" className="uppercase tracking-wide">
                  Tokens ({formatNumber(preview.tokens.length)})
                </Text>
                <Text size="xs" color="muted">␣ = espace</Text>
              </Flex>
              <Box className="max-h-64 overflow-y-auto rounded-lg border border-border bg-muted/20 p-3">
                <Flex wrap gap="xs">
                  {preview.tokens.map((token, index) => (
                    <Box
                      key={`${index}-${preview.tokenIds[index]}`}
                      className="inline-flex items-center gap-1.5 rounded border border-border bg-background px-2 py-0.5"
                      title={token}
                    >
                      <Text as="span" size="xs" mono color="default" className="whitespace-pre">
                        {displayToken(token) || '∅'}
                      </Text>
                      <Text as="span" size="xs" color="muted" mono>
                        {preview.tokenIds[index]}
                      </Text>
                    </Box>
                  ))}
                </Flex>
              </Box>
            </Stack>

            <Stack spacing="sm">
              <Text size="xs" weight="semibold" color="muted" className="uppercase tracking-wide">
                Texte decode
              </Text>
              <Box className="rounded-lg border border-border bg-muted/30 p-3">
                <Text size="sm" color="default" className="whitespace-pre-wrap">
                  {preview.decoded}
                </Text>
              </Box>
            </Stack>
          </Stack>
        )}
      </Stack>
    </Box>
  )
}
