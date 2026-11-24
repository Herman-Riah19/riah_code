import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Flex } from '@/components/atoms/Flex'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { Divider } from '@/components/atoms/Divider'
import { Button } from '@/components/atoms/Button'
import { Input } from '@/components/atoms/Input'
import { Select } from '@/components/atoms/Select'
import { Icon } from '@/components/atoms/Icon'
import { ToggleGroup, type ToggleOption } from '@/components/molecules/ToggleGroup'
import type { ScrapeSource } from '@/types/corpus'

export interface ScrapePanelProps {
  sources: ScrapeSource[]
  selectedSources: string[]
  onSourcesChange: (sources: string[]) => void
  language: string
  availableLanguages: string[]
  onLanguageChange: (language: string) => void
  maxDocuments: number
  onMaxDocumentsChange: (value: number) => void
  onStart: () => void
  isStarting: boolean
  isDisabled?: boolean
  className?: string
}

export const ScrapePanel: React.FC<ScrapePanelProps> = ({
  sources,
  selectedSources,
  onSourcesChange,
  language,
  availableLanguages,
  onLanguageChange,
  maxDocuments,
  onMaxDocumentsChange,
  onStart,
  isStarting,
  isDisabled = false,
  className,
}) => {
  const sourceOptions: ToggleOption[] = sources.map((source) => ({
    value: source.id,
    label: source.label,
  }))

  const allLanguages = availableLanguages.length > 0 ? availableLanguages : ['fr', 'en']

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
            Lancer un nouveau scraping
          </Heading>
          <Text size="sm" color="muted">
            Collectez des donnees depuis vos sources pour alimenter vos corpus d entrainement.
          </Text>
        </Stack>

        <Divider className="mb-2" />

        <Stack spacing="md" className="pt-2">
          <Stack spacing="sm">
            <Flex align="center" justify="between">
              <Text size="sm" weight="semibold" color="default">
                Sources de donnees
              </Text>
              <Text size="xs" color="muted">
                {selectedSources.length} selectionnee(s)
              </Text>
            </Flex>
            <ToggleGroup
              options={sourceOptions}
              value={selectedSources}
              onChange={onSourcesChange}
              multiple
              isDisabled={isDisabled}
            />
            <Flex wrap gap="xs" className="text-xs text-muted-foreground mt-2">
              {selectedSources.map((sourceId) => {
                const source = sources.find((s) => s.id === sourceId)
                if (!source) return null
                return (
                  <Box
                    key={sourceId}
                    className="inline-flex items-center gap-1.5 rounded-full bg-accent/20 px-2.5 py-0.5 text-accent-foreground"
                  >
                    <Icon name="check-icon" size="xs" aria-hidden />
                    <Text size="xs" weight="medium" color="accent">
                      {source.label}
                    </Text>
                  </Box>
                )
              })}
              {selectedSources.length === 0 && (
                <Text size="xs" color="muted">Aucune source selectionnee</Text>
              )}
            </Flex>
          </Stack>

          <Divider className="my-4" />

          <Flex gap="md" wrap className="items-end">
            <Box className="flex-1 min-w-[200px]">
              <Text size="sm" weight="semibold" color="default" className="mb-1 block">
                Langue principale
              </Text>
              <Select
                value={language}
                onChange={(e) => onLanguageChange(e.currentTarget.value)}
                disabled={isDisabled}
              >
                {allLanguages.map((lang) => (
                  <option key={lang} value={lang}>
                    {lang.toUpperCase()}
                  </option>
                ))}
              </Select>
            </Box>

            <Box className="flex-1 min-w-[200px]">
              <Flex align="center" justify="between" className="mb-1">
                <Text size="sm" weight="semibold" color="default">
                  Documents max par langue
                </Text>
                <Text size="xs" color="muted">
                  {maxDocuments.toLocaleString('fr-FR')}
                </Text>
              </Flex>
              <Input
                type="number"
                value={maxDocuments}
                onChange={(e) =>
                  onMaxDocumentsChange(
                    Math.max(1, Math.min(1000000, parseInt(e.currentTarget.value) || 1))
                  )
                }
                disabled={isDisabled}
                min={1}
                max={1000000}
                step={100}
                size="md"
              />
            </Box>
          </Flex>

          <Divider className="my-4" />

          <Flex align="center" justify="end" className="pt-2">
            <Button
              variant="primary"
              size="lg"
              isLoading={isStarting}
              onClick={onStart}
              disabled={isDisabled || selectedSources.length === 0 || isStarting}
              leftIcon={!isStarting && <Icon name="download-icon" size="md" aria-hidden />}
            >
              {isStarting ? 'Demarrage en cours...' : 'Demarrer le scraping'}
            </Button>
          </Flex>
        </Stack>
      </Stack>
    </Box>
  )
}