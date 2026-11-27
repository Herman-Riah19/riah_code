/**
 * Training API client.
 */

import type {
  CheckpointInfo,
  GenerationOutput,
  GeneratePayload,
  ModelPreset,
  TrainResumePayload,
  TrainStartPayload,
  TrainingHistoryEntry,
  TrainingJob,
} from '@/types/training'
import { API_BASE, AUTH_TOKEN, ApiError, readErrorMessage, request } from '@/utils/request-api'

export const trainingApi = {
  /** List all training jobs for the current user. */
  async listJobs(limit = 50): Promise<TrainingJob[]> {
    return request<TrainingJob[]>(`/api/training/jobs?limit=${limit}`)
  },

  /** Start a new training job. */
  async startTraining(payload: TrainStartPayload): Promise<TrainingJob> {
    return request<TrainingJob>('/api/training/jobs', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /** Get a single training job status. */
  async getJob(jobId: string): Promise<TrainingJob> {
    return request<TrainingJob>(`/api/training/jobs/${encodeURIComponent(jobId)}`)
  },

  /** Cancel a training job. */
  async cancelJob(jobId: string): Promise<TrainingJob> {
    return request<TrainingJob>(`/api/training/jobs/${encodeURIComponent(jobId)}/cancel`, {
      method: 'POST',
    })
  },

  /** Resume training from a checkpoint. */
  async resumeTraining(jobId: string, payload: TrainResumePayload): Promise<TrainingJob> {
    return request<TrainingJob>(`/api/training/jobs/${encodeURIComponent(jobId)}/resume`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /** List checkpoints. */
  async listCheckpoints(limit = 50, offset = 0, modelName?: string): Promise<CheckpointInfo[]> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
    if (modelName) params.set('modelName', modelName)
    return request<CheckpointInfo[]>(`/api/training/checkpoints?${params.toString()}`)
  },

  /** Get a single checkpoint. */
  async getCheckpoint(checkpointId: string): Promise<CheckpointInfo> {
    return request<CheckpointInfo>(`/api/training/checkpoints/${encodeURIComponent(checkpointId)}`)
  },

  /** Get available model presets. */
  async listPresets(): Promise<ModelPreset[]> {
    return request<ModelPreset[]>('/api/training/presets')
  },

  /** Get training history from log file. */
  async getHistory(jobId: string): Promise<TrainingHistoryEntry[]> {
    try {
      const payload = await request<{ history: TrainingHistoryEntry[] }>(
        `/api/training/jobs/${encodeURIComponent(jobId)}/history`
      )
      return payload.history
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 404) return []
      throw cause
    }
  },

  /** Stream training progress via SSE using the normal bearer-auth header. */
  streamJob(
    jobId: string,
    onMessage: (data: unknown) => void,
    onDisconnect: () => void,
  ): AbortController {
    const controller = new AbortController()
    const url = `${API_BASE}/api/training/jobs/${encodeURIComponent(jobId)}/stream`

    void (async () => {
      try {
        const response = await fetch(url, {
          headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
          signal: controller.signal,
        })
        if (!response.ok) {
          throw new ApiError(await readErrorMessage(response), response.status)
        }
        if (!response.body) {
          throw new Error('Le navigateur ne permet pas de lire le flux SSE')
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        const dispatchFrames = () => {
          let separator = /\r?\n\r?\n/.exec(buffer)
          while (separator) {
            const frame = buffer.slice(0, separator.index)
            buffer = buffer.slice(separator.index + separator[0].length)
            const data = frame
              .split(/\r?\n/)
              .filter((line) => line.startsWith('data:'))
              .map((line) => line.slice(5).trimStart())
              .join('\n')
            if (data) onMessage(JSON.parse(data) as unknown)
            separator = /\r?\n\r?\n/.exec(buffer)
          }
        }

        try {
          while (!controller.signal.aborted) {
            const { done, value } = await reader.read()
            if (done) break
            buffer += decoder.decode(value, { stream: true })
            dispatchFrames()
          }
          buffer += decoder.decode()
          dispatchFrames()
        } finally {
          reader.releaseLock()
        }
      } catch {
        if (!controller.signal.aborted) onDisconnect()
      }
    })()

    return controller
  },

  /** Generate sample text from a checkpoint for evaluation. */
  async evaluate(jobId: string, payload: GeneratePayload): Promise<GenerationOutput> {
    return request<GenerationOutput>(`/api/training/jobs/${encodeURIComponent(jobId)}/evaluate`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}

/**
 * Hook-friendly SSE connection manager.
 * Returns a controller to start/stop streaming and the latest progress.
 */
export function createTrainingStream(jobId: string) {
  let connection: AbortController | null = null
  const listeners = new Set<(progress: unknown) => void>()

  function start() {
    if (connection) return
    connection = trainingApi.streamJob(
      jobId,
      (data) => listeners.forEach((cb) => cb(data)),
      () => {
      listeners.forEach((cb) => cb({ disconnected: true }))
      },
    )
  }

  function stop() {
    if (connection) {
      connection.abort()
      connection = null
    }
  }

  function subscribe(cb: (progress: unknown) => void) {
    listeners.add(cb)
    return () => listeners.delete(cb)
  }

  return { start, stop, subscribe }
}