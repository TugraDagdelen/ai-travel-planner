import { api } from './api'
import type { AIConnectionResult, AIStatus } from '../types/ai'
import type { Language } from '../types/trip'

export async function fetchAIStatus(signal: AbortSignal) {
  const { data } = await api.get<AIStatus>('/ai/status', { signal })
  return data
}

export async function checkAIConnection(language: Language, signal: AbortSignal) {
  const { data } = await api.post<AIConnectionResult>('/ai/check', { language }, { signal, timeout: 35000 })
  return data
}
