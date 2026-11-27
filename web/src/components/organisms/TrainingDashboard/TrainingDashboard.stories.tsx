import type { Meta, StoryObj } from '@storybook/react'
import { TrainingDashboard } from './TrainingDashboard'
import type { TrainingJob, TrainingHistoryEntry, TrainingProgress } from '@/types/training'

const meta: Meta<typeof TrainingDashboard> = {
  title: 'Organisms/TrainingDashboard',
  component: TrainingDashboard,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    job: { control: 'object' },
    history: { control: 'object' },
    isStreaming: { control: 'boolean' },
  },
}

export default meta
type Story = StoryObj<typeof TrainingDashboard>

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

const mockHistory: TrainingHistoryEntry[] = Array.from({ length: 500 }, (_, i) => ({
  step: (i + 1) * 10,
  epoch: Math.floor(i / 100),
  learningRate: 3e-4 * Math.min(1, (i + 1) / 2000) * (0.5 + 0.5 * Math.cos((Math.PI * i) / 5000)),
  'train/loss': 4.5 * Math.exp(-(i + 1) / 5000) + 1.2 + Math.random() * 0.3,
  'val/valLoss': 4.8 * Math.exp(-(i + 1) / 5000) + 1.5 + Math.random() * 0.2,
}))

const mockJob: TrainingJob = {
  id: 'train_abc123',
  jobType: 'training',
  status: 'running',
  config: {
    trainingConfig: {
      modelConfig: {
        vocabSize: 32000,
        maxSeqLen: 2048,
        nLayers: 12,
        nHeads: 12,
        nKvHeads: null,
        dim: 768,
        dimFF: null,
        normType: 'rmsnorm',
        normEps: 1e-5,
        attnImpl: 'sdpa',
        attnDropout: 0,
        residDropout: 0,
        useBias: false,
        useRoPE: true,
        ropeTheta: 10000,
        ropeScaling: null,
        activation: 'swiglu',
        ffnDropout: 0,
        tieEmbeddings: true,
        initStd: 0.02,
        dtype: 'bf16',
        compileMode: 'default',
        eosTokenId: 0,
        bosTokenId: null,
        padTokenId: 1,
        nParams: 125_000_000,
        headDim: 64,
        resolvedDimFF: 3072,
        resolvedKvHeads: 12,
      },
      trainShards: ['shard_000001.bin', 'shard_000002.bin'],
      valShards: ['shard_val_000001.bin'],
      modelName: 'default',
      batchSize: 32,
      microBatchSize: 8,
      seqLen: 2048,
      numWorkers: 4,
      optimizer: 'adamw',
      lr: 3e-4,
      minLr: 3e-5,
      weightDecay: 0.1,
      beta1: 0.9,
      beta2: 0.95,
      eps: 1e-8,
      gradClip: 1.0,
      scheduler: 'cosine_warmup',
      warmupSteps: 2000,
      decaySteps: 100000,
      maxSteps: 100000,
      maxEpochs: null,
      gradientAccumulationSteps: 4,
      evalInterval: 1000,
      evalSteps: 100,
      logInterval: 10,
      checkpointDir: '/checkpoints/train_abc123',
      checkpointInterval: 5000,
      keepLastNCheckpoints: 3,
      saveOptimizer: true,
      saveRng: true,
      dtype: 'bf16',
      useGradScaler: true,
      compileModel: true,
      tensorboard: false,
      labelSmoothing: 0,
      seed: 42,
    },
    modelName: 'default',
    runId: 'train_abc123',
  },
  userId: 'user-1',
  createdAt: new Date(Date.now() - 3600000).toISOString(),
  startedAt: new Date(Date.now() - 1800000).toISOString(),
  finishedAt: null,
  progress: mockProgress,
  error: null,
  resumeFrom: null,
  result: null,
}

const completedJob: TrainingJob = {
  ...mockJob,
  status: 'completed',
  finishedAt: new Date().toISOString(),
  progress: { ...mockProgress, step: 100000, epoch: 100, progress: 1, loss: 1.42, bestValLoss: 1.58 },
  result: {
    steps: 100000,
    bestValLoss: 1.58,
    tokensSeen: 5_120_000_000,
    elapsedSeconds: 12_600,
    finalLoss: 1.42,
    checkpointDir: '/checkpoints/train_abc123',
    finalCheckpoint: '/checkpoints/train_abc123/checkpoint_final.pt',
    cancelled: false,
  },
}

const failedJob: TrainingJob = {
  ...mockJob,
  status: 'failed',
  finishedAt: new Date().toISOString(),
  progress: { ...mockProgress, step: 12000, loss: 2.8, bestValLoss: 3.1 },
  error: 'CUDA out of memory. Try reducing batch size or using gradient accumulation.',
  result: null,
}

export const Running: Story = {
  args: {
    job: mockJob,
    history: mockHistory,
    isStreaming: true,
    onStart: () => console.log('Start'),
    onCancel: () => console.log('Cancel'),
  },
}

export const Completed: Story = {
  args: {
    job: completedJob,
    history: mockHistory,
    isStreaming: false,
    onResume: () => console.log('Resume'),
    onDismiss: () => console.log('Dismiss'),
  },
}

export const Failed: Story = {
  args: {
    job: failedJob,
    history: mockHistory.slice(0, 1200),
    isStreaming: false,
    onResume: () => console.log('Resume'),
    onDismiss: () => console.log('Dismiss'),
  },
}

export const Empty: Story = {
  args: {
    job: null,
    history: [],
    isStreaming: false,
    onStart: () => console.log('Start'),
  },
}

export const Pending: Story = {
  args: {
    job: { ...mockJob, status: 'pending', startedAt: null, progress: { ...mockProgress, step: 0, loss: null, bestValLoss: null, tokensSeen: 0, learningRate: 3e-4 } },
    history: [],
    isStreaming: false,
    onCancel: () => console.log('Cancel'),
  },
}

export const LargeScale: Story = {
  args: {
    job: {
      ...mockJob,
      config: {
        ...mockJob.config,
        trainingConfig: {
          ...mockJob.config!.trainingConfig!,
          batchSize: 256,
          seqLen: 4096,
          gradientAccumulationSteps: 8,
          maxSteps: 2_000_000,
        },
      },
      progress: { ...mockProgress, step: 1_500_000, maxSteps: 2_000_000, epoch: 1500, progress: 0.75, tokensSeen: 76_800_000_000 },
    },
    history: Array.from({ length: 20000 }, (_, i) => ({
      step: (i + 1) * 100,
      epoch: Math.floor(i / 1000),
      learningRate: 3e-4 * Math.min(1, (i + 1) / 5000),
      'train/loss': 4.5 * Math.exp(-(i + 1) / 20000) + 1.2 + Math.random() * 0.3,
      'val/valLoss': 4.8 * Math.exp(-(i + 1) / 20000) + 1.5 + Math.random() * 0.2,
    })),
    isStreaming: true,
  },
}