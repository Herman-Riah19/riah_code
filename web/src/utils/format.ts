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
