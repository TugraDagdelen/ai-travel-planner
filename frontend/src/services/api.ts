import axios from 'axios'
import type { HealthResponse, TripRequest, ValidatedTripRequest } from '../types/trip'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api',
  timeout: 8000,
})

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>('/health', { signal })
  if (data.status !== 'ok' || data.service !== 'ai-travel-planner') {
    throw new Error('Unexpected backend response')
  }
  return data
}

export async function validatePreferences(request: TripRequest): Promise<ValidatedTripRequest> {
  const { data } = await api.post<ValidatedTripRequest>('/trip-requests/validate', request)
  if (data.status !== 'preferences_validated' || data.itinerary_generated !== false || !data.request) {
    throw new Error('Unexpected validation response')
  }
  return data
}

export function isConnectionError(error: unknown): boolean {
  return axios.isAxiosError(error) && !error.response
}
