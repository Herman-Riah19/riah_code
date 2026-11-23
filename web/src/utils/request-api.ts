export const runtimeEnv = import.meta.env as Record<string, string | undefined>
export const API_BASE = (runtimeEnv.VITE_API_BASE ?? '').replace(/\/+$/, '')
export const AUTH_TOKEN = runtimeEnv.VITE_API_TOKEN ?? 'dev-token'

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export function buildHeaders(init?: HeadersInit): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${AUTH_TOKEN}`,
    ...(init as Record<string, string> | undefined),
  }
}

export async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { error?: { message?: string } }
    return payload.error?.message ?? `Erreur HTTP ${response.status}`
  } catch {
    return `Erreur HTTP ${response.status}`
  }
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: buildHeaders(init.headers),
  })
  if (!response.ok) {
    throw new ApiError(await readErrorMessage(response), response.status)
  }
  return (await response.json()) as T
}
