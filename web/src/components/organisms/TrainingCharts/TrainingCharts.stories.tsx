import type { Meta, StoryObj } from '@storybook/react'
import { TrainingCharts } from './TrainingCharts'
import type { TrainingHistoryEntry, TrainingProgress } from '@/types/training'

const meta: Meta<typeof TrainingCharts> = {
  title: 'Organisms/TrainingCharts',
  component: TrainingCharts,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    history: { control: 'object' },
    currentProgress: { control: 'object' },
    maxSteps: { control: 'number' },
  },
}

export default meta
type Story = StoryObj<typeof TrainingCharts>

const generateMockHistory = (steps: number): TrainingHistoryEntry[] => {
  const history: TrainingHistoryEntry[] = []
  for (let i = 1; i <= steps; i++) {
    const baseLoss = 4.5 * Math.exp(-i / 5000) + 1.2 + Math.random() * 0.3
    const valLoss = baseLoss + 0.3 + Math.random() * 0.2
    const lr = 3e-4 * Math.min(1, i / 2000) * (0.5 + 0.5 * Math.cos((Math.PI * i) / 100000))
    history.push({
      step: i * 10,
      epoch: Math.floor(i / 100),
      learningRate: lr,
      'train/loss': baseLoss,
      'val/valLoss': valLoss,
    })
  }
  return history
}

const mockProgress: TrainingProgress = {
  step: 45000,
  epoch: 45,
  maxSteps: 100000,
  progress: 0.45,
  loss: 1.85,
  bestValLoss: 2.12,
  tokensSeen: 2_304_000_000,
  learningRate: 1.2e-4,
  cancelled: false,
}

export const WithData: Story = {
  args: {
    history: generateMockHistory(5000),
    currentProgress: mockProgress,
    maxSteps: 100000,
  },
}

export const EarlyTraining: Story = {
  args: {
    history: generateMockHistory(200),
    currentProgress: { ...mockProgress, step: 2000, epoch: 2, progress: 0.02, loss: 3.8, bestValLoss: 4.1, tokensSeen: 102_400_000, learningRate: 1.5e-4 },
    maxSteps: 100000,
  },
}

export const NearCompletion: Story = {
  args: {
    history: generateMockHistory(9500),
    currentProgress: { ...mockProgress, step: 95000, epoch: 95, progress: 0.95, loss: 1.42, bestValLoss: 1.58, tokensSeen: 4_864_000_000, learningRate: 3e-5 },
    maxSteps: 100000,
  },
}

export const Empty: Story = {
  args: {
    history: [],
    currentProgress: { step: 0, epoch: 0, maxSteps: 100000, progress: 0, loss: null, bestValLoss: null, tokensSeen: 0, learningRate: 3e-4, cancelled: false },
    maxSteps: 100000,
  },
}

export const OnlyTrainingLoss: Story = {
  args: {
    history: generateMockHistory(1000).map((h) => ({ ...h, 'val/valLoss': undefined })),
    currentProgress: { ...mockProgress, bestValLoss: null },
    maxSteps: 100000,
  },
}

export const WithVeryHighSteps: Story = {
  args: {
    history: generateMockHistory(20000),
    currentProgress: { ...mockProgress, step: 1_500_000, maxSteps: 2_000_000, epoch: 1500, progress: 0.75, tokensSeen: 76_800_000_000 },
    maxSteps: 2_000_000,
  },
}