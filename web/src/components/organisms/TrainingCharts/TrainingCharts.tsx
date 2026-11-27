import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  Cell,
} from 'recharts'
import { Box } from '@/components/atoms/Box'
import { Heading } from '@/components/atoms/Heading'
import { Text } from '@/components/atoms/Text'
import { Flex } from '@/components/atoms/Flex'
import { Badge } from '@/components/atoms/Badge'
import { Divider } from '@/components/atoms/Divider'
import { Stack } from '@/components/atoms/Stack'
import { formatNumber } from '@/utils/format'
import type { TrainingHistoryEntry, TrainingProgress } from '@/types/training'

interface MetricSeries {
  name: string
  data: Array<{ step: number; value: number }>
  color: string
}

export interface TrainingChartsProps {
  history: TrainingHistoryEntry[]
  currentProgress: TrainingProgress | null
  maxSteps: number
  className?: string
}

const LOSS_COLOR = '#ef4444'
const VAL_LOSS_COLOR = '#3b82f6'
const LR_COLOR = '#8b5cf6'
const THROUGHPUT_COLOR = '#22c55e'

function toSeries(history: TrainingHistoryEntry[], key: string, color: string): MetricSeries {
  const data = history
    .filter((entry) => entry[key] !== undefined)
    .map((entry) => ({
      step: entry.step,
      value: Number(entry[key]),
    }))
  return { name: key, data, color }
}

export function TrainingCharts({
  history,
  currentProgress,
  maxSteps,
  className,
}: TrainingChartsProps) {
  const lossSeries = toSeries(history, 'train/loss', LOSS_COLOR)
  const valLossSeries = toSeries(history, 'val/valLoss', VAL_LOSS_COLOR)
  const lrSeries = toSeries(history, 'learningRate', LR_COLOR)

  const hasLossData = lossSeries.data.length > 0
  const hasValLossData = valLossSeries.data.length > 0
  const hasLrData = lrSeries.data.length > 0

  const currentStep = currentProgress?.step ?? 0
  const currentLoss = currentProgress?.loss ?? null
  const currentValLoss = currentProgress?.bestValLoss ?? null
  const currentLr = currentProgress?.learningRate ?? null

  const progressPercent = maxSteps > 0 ? Math.min(100, (currentStep / maxSteps) * 100) : 0

  return (
    <Box
      className={['rounded-xl border border-border bg-card p-6 shadow-sm', className].filter(Boolean).join(' ')}
    >
      <Flex align="start" justify="between" gap="md" className="mb-6">
        <Stack spacing="xs">
          <Heading level={2} size="lg" weight="semibold">
            Metriques d'entrainement
          </Heading>
          <Text size="sm" color="muted">
            Historique complet + position actuelle (step {formatNumber(currentStep)} / {formatNumber(maxSteps)})
          </Text>
        </Stack>
        <Box className="flex items-center gap-2">
          <Badge variant="accent" size="sm" dot>
            {progressPercent.toFixed(1)}%
          </Badge>
          <Text size="sm" color="muted" className="font-mono">
            {formatNumber(currentStep)} / {formatNumber(maxSteps)}
          </Text>
        </Box>
      </Flex>

      <Divider className="mb-6" />

      <Stack spacing="lg">
        {/* Loss Chart */}
        {(hasLossData || hasValLossData) && (
          <Box>
            <Flex align="center" justify="between" gap="md" className="mb-3">
              <Heading level={3} size="md" weight="semibold">
                Loss (entrainement & validation)
              </Heading>
              <Flex align="center" gap="md" className="text-xs">
                <Badge variant="success" size="sm" dot>
                  Train
                </Badge>
                {hasValLossData && <Badge variant="default" size="sm" dot>Val</Badge>}
                <Text color="muted">
                  Step actuel: {currentLoss !== null ? currentLoss.toFixed(4) : 'N/A'}
                  {currentValLoss !== null ? ` | Best Val: ${currentValLoss.toFixed(4)}` : ''}
                </Text>
              </Flex>
            </Flex>
            <Box className="relative h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={lossSeries.data}
                  margin={{ top: 10, right: 30, left: 20, bottom: 20 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="step"
                    type="number"
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    tickFormatter={formatNumber}
                    axisLine={{ stroke: '#e5e7eb' }}
                    tickLine={false}
                  />
                  <YAxis
                    type="number"
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    tickFormatter={(v) => v.toFixed(2)}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    formatter={(value) => [formatNumber(value as number), '']}
                    labelFormatter={(step) => `Step ${formatNumber(step as number)}`}
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                    }}
                  />
                  <Legend
                    wrapperStyle={{ paddingTop: '20px' }}
                    formatter={(value) => (
                      <Text size="xs" color="default">
                        {value}
                      </Text>
                    )}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke={LOSS_COLOR}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 6 }}
                    name="Train Loss"
                    connectNulls={true}
                  />
                  {hasValLossData && (
                    <Line
                      type="monotone"
                      dataKey="value"
                      data={valLossSeries.data}
                      stroke={VAL_LOSS_COLOR}
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={false}
                      activeDot={{ r: 6 }}
                      name="Val Loss"
                      connectNulls={true}
                    >
                      {valLossSeries.data.map((_, index) => (
                        <Cell key={index} fill={VAL_LOSS_COLOR} />
                      ))}
                    </Line>
                  )}
                  {currentLoss !== null && (
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke={LOSS_COLOR}
                      strokeWidth={2}
                      dot={false}
                      data={[{ step: currentStep, value: currentLoss }]}
                      isAnimationActive={false}
                    >
                      <Cell key="current" fill={LOSS_COLOR} />
                    </Line>
                  )}
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Box>
        )}

        {/* Learning Rate Chart */}
        {hasLrData && (
          <Box>
            <Flex align="center" justify="between" gap="md" className="mb-3">
              <Heading level={3} size="md" weight="semibold">
                Learning Rate Schedule
              </Heading>
              <Text size="xs" color="muted" className="font-mono">
                LR actuel: {currentLr !== null ? currentLr.toExponential(2) : 'N/A'}
              </Text>
            </Flex>
            <Box className="relative h-[200px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={lrSeries.data}
                  margin={{ top: 10, right: 30, left: 20, bottom: 20 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="step"
                    type="number"
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    tickFormatter={formatNumber}
                    axisLine={{ stroke: '#e5e7eb' }}
                    tickLine={false}
                  />
                  <YAxis
                    type="number"
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    tickFormatter={(v) => (typeof v === 'number' ? v.toExponential(1) : '')}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    formatter={(value) => [
                      typeof value === 'number' ? value.toExponential(3) : String(value ?? ''),
                      'LR',
                    ]}
                    labelFormatter={(step) => `Step ${formatNumber(step as number)}`}
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke={LR_COLOR}
                    fill={LR_COLOR}
                    fillOpacity={0.15}
                    strokeWidth={2}
                    connectNulls={true}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Box>
          </Box>
        )}

        {/* Perplexity Chart (derived from loss) */}
        {(hasLossData || hasValLossData) && (
          <Box>
            <Flex align="center" justify="between" gap="md" className="mb-3">
              <Heading level={3} size="md" weight="semibold">
                Perplexite (exp(Loss))
              </Heading>
              <Flex align="center" gap="md" className="text-xs">
                <Text color="muted" className="font-mono">
                  Ppl train: {currentLoss !== null ? Math.exp(currentLoss).toFixed(1) : 'N/A'}
                  {currentValLoss !== null ? ` | Ppl val: ${Math.exp(currentValLoss).toFixed(1)}` : ''}
                </Text>
              </Flex>
            </Flex>
            <Box className="relative h-[200px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={lossSeries.data.map((d) => ({ step: d.step, value: Math.exp(d.value) }))}
                  margin={{ top: 10, right: 30, left: 20, bottom: 20 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="step"
                    type="number"
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    tickFormatter={formatNumber}
                    axisLine={{ stroke: '#e5e7eb' }}
                    tickLine={false}
                  />
                  <YAxis
                    type="number"
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    tickFormatter={(v) => formatNumber(v)}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    formatter={(value) => [formatNumber(Number(value)), 'Perplexite']}
                    labelFormatter={(step) => `Step ${formatNumber(step as number)}`}
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke={LOSS_COLOR}
                    strokeWidth={2}
                    dot={false}
                    connectNulls={true}
                    name="Train Perplexite"
                  />
                  {hasValLossData && (
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke={VAL_LOSS_COLOR}
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={false}
                      data={valLossSeries.data.map((d) => ({ step: d.step, value: Math.exp(d.value) }))}
                      connectNulls={true}
                      name="Val Perplexite"
                    >
                      {valLossSeries.data.map((_, index) => (
                        <Cell key={index} fill={VAL_LOSS_COLOR} />
                      ))}
                    </Line>
                  )}
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Box>
        )}

        {/* Tokens/Step throughput bar chart */}
        {history.length > 0 && (
          <Box>
            <Flex align="center" justify="between" gap="md" className="mb-3">
              <Heading level={3} size="md" weight="semibold">
                Debit (tokens vus par step)
              </Heading>
              <Text size="xs" color="muted" className="font-mono">
                Total: {formatNumber(currentProgress?.tokensSeen ?? 0)}
              </Text>
            </Flex>
            <Box className="relative h-[200px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={history.map((entry, i) => ({
                    step: entry.step,
                    tokens: entry.step > 0 ? entry.step * 32 : 0,
                    index: i,
                  }))}
                  margin={{ top: 10, right: 30, left: 20, bottom: 20 }}
                  layout="vertical"
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                  <XAxis
                    type="number"
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    tickFormatter={(v) => formatNumber(v)}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    dataKey="step"
                    type="number"
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    tickFormatter={formatNumber}
                    axisLine={{ stroke: '#e5e7eb' }}
                    tickLine={false}
                    reversed
                  />
                  <Tooltip
                    formatter={(value) => [formatNumber(Number(value)), 'Tokens']}
                    labelFormatter={(step) => `Step ${formatNumber(step as number)}`}
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                    }}
                  />
                  <Bar
                    dataKey="tokens"
                    fill={THROUGHPUT_COLOR}
                    radius={[0, 4, 4, 0]}
                    maxBarSize={30}
                  />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Box>
        )}

        {/* Empty state */}
        {!hasLossData && !hasValLossData && !hasLrData && (
          <Box className="py-12 text-center">
            <Stack spacing="sm" align="center">
              <Text size="lg" color="muted" weight="medium">
                Aucune metrique disponible
              </Text>
              <Text size="sm" color="muted">
                Les graphiques apparaitront apres les premieres iterations d'entrainement.
              </Text>
              <Text size="xs" color="muted" className="font-mono">
                Intervalle de log: {currentProgress ? 'config.logInterval steps' : 'N/A'}
              </Text>
            </Stack>
          </Box>
        )}
      </Stack>
    </Box>
  )
}