import axios from 'axios'
import { api } from './api'
import type { Category, DataMode, DestinationResponse, PlacesResponse, WeatherResponse } from '../types/discovery'
import type { Language } from '../types/trip'

export interface DataError { code: string; retryAfter: number }

export function dataError(error: unknown): DataError {
  if (axios.isAxiosError(error)) {
    return { code: error.response?.data?.code || 'network', retryAfter: error.response?.data?.retry_after_seconds || 0 }
  }
  return { code: 'provider_invalid_response', retryAfter: 0 }
}

export async function searchDestinations(q: string, countryCode: string, language: Language, mode: DataMode, signal: AbortSignal) {
  const { data } = await api.get<DestinationResponse>('/destinations', { params: { q, country_code: countryCode || undefined, language, mode }, signal, timeout: 30000 })
  return data
}

export async function fetchWeather(destinationId: string, start: string, end: string, mode: DataMode, signal: AbortSignal) {
  const { data } = await api.get<WeatherResponse>('/weather', { params: { destination_id: destinationId, start_date: start, end_date: end, mode }, signal, timeout: 30000 })
  return data
}

export async function fetchPlaces(destinationId: string, categories: Category[], mode: DataMode, signal: AbortSignal) {
  const params = new URLSearchParams({ destination_id: destinationId, radius_m: '10000', mode })
  categories.forEach(category => params.append('categories', category))
  const { data } = await api.get<PlacesResponse>('/places', { params, signal, timeout: 75000 })
  return data
}
