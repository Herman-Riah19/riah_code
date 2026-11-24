/**
 * Shared job contracts rendered by the generic `JobMonitor` organism.
 *
 * Every module job (corpus pipeline, tokenizer training, encoding...) extends
 * `MonitorableJob` so a single presentation component can display them all.
 */

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface MonitorableJob {
  id: string
  jobType: string
  status: JobStatus
  config: Record<string, unknown>
  userId: string | null
  createdAt: string
  startedAt: string | null
  finishedAt: string | null
  /**
   * Module-specific progress counters keyed by metric name.
   * Typed as `object` so dedicated progress interfaces stay assignable.
   */
  progress: object
  error: string | null
}

/** One configuration entry displayed by the job monitor. */
export interface JobConfigField {
  key: string
  label: string
  icon?: string
}
