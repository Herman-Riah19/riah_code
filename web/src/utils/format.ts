const NUMBER_FORMATTER = new Intl.NumberFormat('fr-FR')
const DATE_FORMATTER = new Intl.DateTimeFormat('fr-FR', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

const BYTE_UNITS = ['o', 'Ko', 'Mo', 'Go', 'To'] as const

export function formatNumber(value: number): string {
  if (!Number.isFinite(value)) return '0'
  return NUMBER_FORMATTER.format(value)
}

export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return `0 ${BYTE_UNITS[0]}`
  const exponent = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    BYTE_UNITS.length - 1,
  )
  const size = bytes / 1024 ** exponent
  const digits = exponent === 0 ? 0 : 1
  return `${size.toFixed(digits)} ${BYTE_UNITS[exponent]}`
}

export function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return DATE_FORMATTER.format(date)
}

export function formatTokensPerStep(batchSize: number, seqLen: number): string {
  const tokens = batchSize * seqLen
  return tokens >= 1e6 ? `${(tokens / 1e6).toFixed(1)}M` : tokens >= 1e3 ? `${(tokens / 1e3).toFixed(0)}k` : String(tokens)
}

export function formatTotalTokens(batchSize: number, seqLen: number, maxSteps: number): string {
  const total = batchSize * seqLen * maxSteps
  if (total >= 1e9) return `${(total / 1e9).toFixed(2)}B`
  if (total >= 1e6) return `${(total / 1e6).toFixed(1)}M`
  if (total >= 1e3) return `${(total / 1e3).toFixed(1)}k`
  return String(total)
}

export function formatBillionProgress(batchSize: number, seqLen: number, maxSteps: number): string {
  const total = batchSize * seqLen * maxSteps
  const pct = (total / 1e9) * 100
  return `${pct.toFixed(1)}%`
}
