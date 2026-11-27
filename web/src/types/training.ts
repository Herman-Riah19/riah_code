/**
 * Training module types - domain models and API contracts.
 */

import type { JobStatus } from '@/types/job'

/** Training job progress snapshot (matches backend TrainingLoop.snapshot()). */
export interface TrainingProgress {
  step: number
  epoch: number
  maxSteps: number
  progress: number
  loss: number | null
  bestValLoss: number | null
  tokensSeen: number
  learningRate: number
  cancelled: boolean
}

/** Single entry from training_log.jsonl */
export interface TrainingHistoryEntry {
  step: number
  epoch: number
  learningRate: number
  'train/loss'?: number
  'val/valLoss'?: number
  [key: string]: unknown
}

/** Training job as returned by the API. */
export interface TrainingJob {
  id: string
  jobType: string
  status: JobStatus
  config: TrainingJobConfig
  userId: string | null
  createdAt: string
  startedAt: string | null
  finishedAt: string | null
  progress: TrainingProgress
  error: string | null
  resumeFrom: string | null
  result: TrainingJobResult | null
}

/** Configuration stored in the job. */
export interface TrainingJobConfig {
  trainingConfig: TrainingConfig
  modelName: string
  runId: string
  resumeFrom?: string
}

/** Training configuration (mirrors backend TrainingConfig). */
export interface TrainingConfig {
  modelConfig: ModelConfig
  trainShards: string[]
  valShards: string[]
  modelName: string
  batchSize: number
  microBatchSize: number | null
  seqLen: number
  numWorkers: number
  optimizer: 'adamw' | 'adamw8bit' | 'lion'
  lr: number
  minLr: number
  weightDecay: number
  beta1: number
  beta2: number
  eps: number
  gradClip: number
  scheduler: 'cosine' | 'cosine_warmup' | 'constant' | 'wsd'
  warmupSteps: number
  decaySteps: number
  maxSteps: number
  maxEpochs: number | null
  gradientAccumulationSteps: number
  evalInterval: number
  evalSteps: number
  logInterval: number
  checkpointDir: string
  checkpointInterval: number
  keepLastNCheckpoints: number
  saveOptimizer: boolean
  saveRng: boolean
  dtype: 'fp32' | 'fp16' | 'bf16'
  useGradScaler: boolean
  compileModel: boolean
  tensorboard: boolean
  labelSmoothing: number
  seed: number
}

/** Model architecture configuration. */
export interface ModelConfig {
  vocabSize: number
  maxSeqLen: number
  nLayers: number
  nHeads: number
  nKvHeads: number | null
  dim: number
  dimFF: number | null
  normType: 'rmsnorm' | 'layernorm'
  normEps: number
  attnImpl: 'eager' | 'flash' | 'sdpa'
  attnDropout: number
  residDropout: number
  useBias: boolean
  useRoPE: boolean
  ropeTheta: number
  ropeScaling: Record<string, number> | null
  activation: 'gelu' | 'swiglu' | 'geglu'
  ffnDropout: number
  tieEmbeddings: boolean
  initStd: number
  dtype: 'fp32' | 'fp16' | 'bf16'
  compileMode: 'default' | 'reduce-overhead' | 'max-autotune' | null
  eosTokenId: number
  bosTokenId: number | null
  padTokenId: number
  nParams: number
  headDim: number
  resolvedDimFF: number
  resolvedKvHeads: number
}

/** Training job result payload. */
export interface TrainingJobResult {
  steps: number
  bestValLoss: number
  tokensSeen: number
  elapsedSeconds: number
  finalLoss: number | null
  checkpointDir: string
  finalCheckpoint: string
  cancelled: boolean
}

/** Preset model architecture. */
export interface ModelPreset {
  name: string
  parameters: number
  modelConfig: ModelConfig
}

/** Checkpoint metadata. */
export interface CheckpointInfo {
  id: string
  path: string
  step: number
  epoch: number
  loss: number
  valLoss: number | null
  modelConfig: ModelConfig
  trainingConfig: TrainingConfig | null
  createdAt: string
  isBest: boolean
  modelName: string | null
  metadata: Record<string, unknown>
}

/** Payload to start a training job. */
export interface TrainStartPayload {
  preset: string
  modelConfig?: Record<string, unknown>
  modelName: string
  trainShards?: string[]
  valShards?: string[]
  batchSize: number
  microBatchSize?: number
  seqLen: number
  numWorkers: number
  optimizer: 'adamw' | 'adamw8bit' | 'lion'
  lr: number
  minLr: number
  weightDecay: number
  beta1: number
  beta2: number
  eps: number
  gradClip: number
  scheduler: 'cosine' | 'cosine_warmup' | 'constant' | 'wsd'
  warmupSteps: number
  decaySteps: number
  maxSteps: number
  maxEpochs?: number
  gradientAccumulationSteps: number
  evalInterval: number
  evalSteps: number
  logInterval: number
  checkpointInterval: number
  keepLastNCheckpoints: number
  saveOptimizer: boolean
  saveRng: boolean
  dtype: 'fp32' | 'fp16' | 'bf16'
  useGradScaler: boolean
  compileModel: boolean
  tensorboard: boolean
  labelSmoothing: number
  seed: number
}

/** Payload to resume a training job. */
export interface TrainResumePayload {
  checkpointId?: string
  maxSteps?: number
  lr?: number
}

/** Payload to generate/evaluate from a checkpoint. */
export interface GeneratePayload {
  prompt: string
  checkpointId?: string
  maxTokens: number
  temperature: number
  topK?: number
  topP: number
  repetitionPenalty: number
  stopSequences: string[]
  seed?: number
}

/** Generation output. */
export interface GenerationOutput {
  prompt: string
  completion: string
  text: string
  generatedTokens: number
  checkpointId: string
}

/** Training dashboard state. */
export interface TrainingDashboardState {
  jobs: TrainingJob[]
  activeJob: TrainingJob | null
  history: TrainingHistoryEntry[]
  checkpoints: CheckpointInfo[]
  presets: ModelPreset[]
  isLoading: boolean
  isSubmitting: boolean
  isStreaming: boolean
  error: string | null

  // Form state
  preset: string
  modelName: string
  batchSize: number
  seqLen: number
  maxSteps: number
  lr: number
  warmupSteps: number
  evalInterval: number
  checkpointInterval: number
  dtype: 'fp32' | 'fp16' | 'bf16'

  // Evaluation
  evalPrompt: string
  evalResult: GenerationOutput | null
  isEvaluating: boolean
}