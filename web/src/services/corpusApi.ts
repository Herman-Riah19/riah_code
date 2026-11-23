import type {
  CorpusDataset,
  CorpusJob,
  ScrapeSource,
  StartPipelinePayload,
} from '@/types/corpus'
import { request } from '@/utils/request-api'


export const corpusApi = {
  async listDatasets(): Promise<CorpusDataset[]> {
    const payload = await request<{ datasets: CorpusDataset[] }>('/api/corpus/datasets')
    return payload.datasets
  },

  async listSources(): Promise<ScrapeSource[]> {
    const payload = await request<{ sources: ScrapeSource[] }>('/api/corpus/sources')
    return payload.sources
  },

  async startPipeline(options: StartPipelinePayload): Promise<CorpusJob> {
    return request<CorpusJob>('/api/corpus/pipeline/start', {
      method: 'POST',
      body: JSON.stringify(options),
    })
  },

  async getJobStatus(jobId: string): Promise<CorpusJob> {
    return request<CorpusJob>(
      `/api/corpus/pipeline/${encodeURIComponent(jobId)}/status`,
    )
  },

  async resumePipeline(jobId: string): Promise<CorpusJob> {
    return request<CorpusJob>(
      `/api/corpus/pipeline/${encodeURIComponent(jobId)}/resume`,
      { method: 'POST' },
    )
  },
}
