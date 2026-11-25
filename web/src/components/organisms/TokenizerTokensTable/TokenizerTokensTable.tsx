import { useState, useEffect } from 'react'
import { Text } from '@/components/atoms/Text'
import { Badge } from '@/components/atoms/Badge'
import { formatNumber } from '@/utils/format'
import { DataTableOrganism } from '@/components/organisms/DataTableOrganism'
import type { DataTableColumn } from '@/components/molecules/DataTable'
import { tokenizerApi } from '@/services/tokenizerApi'
import type { TokenizerVocabEntry } from '@/types/tokenizer'

export interface TokenizerTokensTableProps {
  /** Token entries to display. When omitted, loaded from the backend /api/tokenizer/vocab. */
  tokens?: TokenizerVocabEntry[]
  isLoading?: boolean
  className?: string
}

const COLUMNS: DataTableColumn<TokenizerVocabEntry>[] = [
  {
    key: 'token',
    label: 'Token',
    cell: (value) => (
      <Text as="span" size="sm" mono color="default" className="whitespace-pre">
        {String(value) || '∅'}
      </Text>
    ),
  },
  {
    key: 'tokenId',
    label: 'ID',
    align: 'right',
    cell: (value) => (
      <Text size="sm" color="muted" className="font-mono">
        {formatNumber(Number(value))}
      </Text>
    ),
  },
  {
    key: 'source',
    label: 'Source',
    sortable: false,
    cell: () => (
      <Badge variant="muted" size="sm">
        vocab
      </Badge>
    ),
  },
  {
    key: 'language',
    label: 'Langue',
    sortable: false,
    cell: () => (
      <Badge variant="default" size="sm">
        —
      </Badge>
    ),
  },
  {
    key: 'frequency',
    label: 'Frequence',
    align: 'right',
    sortable: false,
    cell: () => (
      <Text size="sm" color="muted" className="font-mono">
        —
      </Text>
    ),
  },
  {
    key: 'firstSeen',
    label: 'Premiere apparition',
    sortable: false,
    cell: () => (
      <Text size="sm" color="muted" className="font-mono">
        —
      </Text>
    ),
  },
]

export const TokenizerTokensTable: React.FC<TokenizerTokensTableProps> = ({
  tokens: tokensProp,
  isLoading = false,
  className,
}) => {
  const [tokens, setTokens] = useState<TokenizerVocabEntry[] | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    if (tokensProp) return
    void (async () => {
      try {
        const vocab = await tokenizerApi.getVocab()
        setTokens(vocab)
      } catch (cause) {
        setLoadError(cause instanceof Error ? cause.message : 'Erreur inattendue')
      }
    })()
  }, [tokensProp])

  const displayTokens = tokensProp ?? tokens ?? []
  const isLoadingData = isLoading || (tokens === null && !tokensProp)

  return (
    <DataTableOrganism
      className={className}
      title="Explorateur de tokens"
      description={
        loadError
          ? `Impossible de charger le vocabulaire : ${loadError}`
          : `Liste des ${formatNumber(displayTokens.length)} tokens du vocabulaire entraine (charges depuis l API).`
      }
      badge={{
        variant: loadError ? 'error' : 'accent',
        label: `${formatNumber(displayTokens.length)} token(s)`,
      }}
      columns={COLUMNS}
      data={displayTokens}
      pageSize={10}
      isLoading={isLoadingData}
      emptyMessage="Aucun token trouve."
      searchPlaceholder="Rechercher un token..."
      rowKey={(entry) => `${entry.tokenId}-${entry.token}`}
    />
  )
}

export default TokenizerTokensTable
