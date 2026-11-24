import type {
  EncodeCorpusPayload,
  TokenPreview,
  TokenizerJob,
  TokenizerVocabInfo,
  TrainTokenizerPayload,
} from '@/types/tokenizer'
import { ApiError, request } from '@/utils/request-api'

interface TokenizerInfoResponse {
  exists: boolean
  vocabInfo?: TokenizerVocabInfo
}

export const tokenizerApi = {
  async getInfo(): Promise<TokenizerVocabInfo | null> {
    try {
      const payload = await request<TokenizerInfoResponse>('/api/tokenizer/info')
      return payload.vocabInfo ?? null
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 404) return null
      throw cause
    }
  },

  async train(payload: TrainTokenizerPayload): Promise<TokenizerJob> {
    return request<TokenizerJob>('/api/tokenizer/train', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async encode(payload: EncodeCorpusPayload): Promise<TokenizerJob> {
    return request<TokenizerJob>('/api/tokenizer/encode', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async getJobStatus(jobId: string): Promise<TokenizerJob> {
    return request<TokenizerJob>(
      `/api/tokenizer/status/${encodeURIComponent(jobId)}`,
    )
  },

  async preview(text: string): Promise<TokenPreview> {
    return request<TokenPreview>('/api/tokenizer/preview', {
      method: 'POST',
      body: JSON.stringify({ text }),
    })
  },
}
