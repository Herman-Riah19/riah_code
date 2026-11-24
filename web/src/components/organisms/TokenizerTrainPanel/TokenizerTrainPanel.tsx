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
import { ToggleGroup, type ToggleOption } from '@/components/molecules/ToggleGroup'

export interface TokenizerTrainPanelProps {
  vocabSize: number
  onVocabSizeChange: (value: number) => void
  minFrequency: number
  onMinFrequencyChange: (value: number) => void
  corpusSampleSize: number
  onCorpusSampleSizeChange: (value: number) => void
  numThreads: number
  onNumThreadsChange: (value: number) => void
  languages: string[]
  onLanguagesChange: (languages: string[]) => void
  availableLanguages: string[]
  onTrain: () => void
  isStarting: boolean
  isDisabled?: boolean
  className?: string
}

function clampNumber(raw: string, min: number, max: number, onChange: (value: number) => void): void {
  const parsed = Number.parseInt(raw, 10)
  if (Number.isNaN(parsed)) return
  onChange(Math.min(max, Math.max(min, parsed)))
}

export const TokenizerTrainPanel: React.FC<TokenizerTrainPanelProps> = ({
  vocabSize,
  onVocabSizeChange,
  minFrequency,
  onMinFrequencyChange,
  corpusSampleSize,
  onCorpusSampleSizeChange,
  numThreads,
  onNumThreadsChange,
  languages,
  onLanguagesChange,
  availableLanguages,
  onTrain,
  isStarting,
  isDisabled = false,
  className,
}) => {
  const languageOptions: ToggleOption[] = (
    availableLanguages.length > 0 ? availableLanguages : ['fr', 'en']
  ).map((language) => ({ value: language, label: language.toUpperCase() }))

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
            Entrainer un tokenizer BPE
          </Heading>
          <Text size="sm" color="muted">
            Apprenez un vocabulaire byte-level a partir du corpus nettoye.
          </Text>
        </Stack>

        <Divider className="mb-2" />

        <Box className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Stack spacing="xs">
            <Text size="sm" weight="semibold" color="default">
              Taille du vocabulaire
            </Text>
            <Input
              type="number"
              value={vocabSize}
              min={256}
              max={200000}
              step={1000}
              disabled={isDisabled}
              onChange={(event) => clampNumber(event.currentTarget.value, 256, 200000, onVocabSizeChange)}
            />
          </Stack>

          <Stack spacing="xs">
            <Text size="sm" weight="semibold" color="default">
              Frequence minimale
            </Text>
            <Input
              type="number"
              value={minFrequency}
              min={1}
              max={100}
              disabled={isDisabled}
              onChange={(event) => clampNumber(event.currentTarget.value, 1, 100, onMinFrequencyChange)}
            />
          </Stack>

          <Stack spacing="xs">
            <Text size="sm" weight="semibold" color="default">
              Echantillon du corpus
            </Text>
            <Input
              type="number"
              value={corpusSampleSize}
              min={1}
              max={1000000}
              step={1000}
              disabled={isDisabled}
              onChange={(event) =>
                clampNumber(event.currentTarget.value, 1, 1000000, onCorpusSampleSizeChange)
              }
            />
          </Stack>

          <Stack spacing="xs">
            <Text size="sm" weight="semibold" color="default">
              Threads
            </Text>
            <Input
              type="number"
              value={numThreads}
              min={1}
              max={64}
              disabled={isDisabled}
              onChange={(event) => clampNumber(event.currentTarget.value, 1, 64, onNumThreadsChange)}
            />
          </Stack>
        </Box>

        <Divider className="my-2" />

        <Stack spacing="sm">
          <Flex align="center" justify="between">
            <Text size="sm" weight="semibold" color="default">
              Langues du corpus
            </Text>
            <Text size="xs" color="muted">
              {languages.length} selectionnee(s)
            </Text>
          </Flex>
          <ToggleGroup
            options={languageOptions}
            value={languages}
            onChange={onLanguagesChange}
            multiple
            isDisabled={isDisabled}
          />
        </Stack>

        <Flex align="center" justify="end" className="pt-2">
          <Button
            variant="primary"
            size="lg"
            isLoading={isStarting}
            onClick={onTrain}
            disabled={isDisabled || isStarting || languages.length === 0}
            leftIcon={!isStarting && <Icon name="sparkles-icon" size="md" aria-hidden />}
          >
            {isStarting ? 'Entrainement en cours...' : 'Entrainer le tokenizer'}
          </Button>
        </Flex>
      </Stack>
    </Box>
  )
}
