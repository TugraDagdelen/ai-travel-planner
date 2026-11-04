import axios from 'axios'
import { api } from './api'
import type { GenerateTripRequest, TripList, TripRecord } from '../types/itinerary'
import type { Place } from '../types/discovery'

export interface TripOperationError { code: string; message: string; retryable: boolean }

export async function generateTrip(body: GenerateTripRequest): Promise<TripRecord> {
  const { data } = await api.post<TripRecord>('/trips/generate', body, { timeout: 90000 })
  return data
}

export async function reviseTrip(id: string, instruction: string): Promise<TripRecord> {
  const { data } = await api.post<TripRecord>(`/trips/${encodeURIComponent(id)}/revise`, { instruction }, { timeout: 90000 })
  return data
}

export async function getTripPlaces(id: string): Promise<Place[]> {
  const { data } = await api.get<Place[]>(`/trips/${encodeURIComponent(id)}/places`)
  return data
}

export async function editTripActivity(id: string, action: 'add' | 'remove', date: string, placeId: string): Promise<TripRecord> {
  const { data } = await api.patch<TripRecord>(`/trips/${encodeURIComponent(id)}/activities`, { action, date, place_id: placeId })
  return data
}

export async function listTrips(): Promise<TripList> {
  const { data } = await api.get<TripList>('/trips')
  return data
}

export async function getTrip(id: string): Promise<TripRecord> {
  const { data } = await api.get<TripRecord>(`/trips/${encodeURIComponent(id)}`)
  return data
}

export async function renameTrip(id: string, title: string): Promise<TripRecord> {
  const { data } = await api.patch<TripRecord>(`/trips/${encodeURIComponent(id)}`, { title })
  return data
}

export async function deleteTrip(id: string): Promise<void> {
  await api.delete(`/trips/${encodeURIComponent(id)}`)
}

export function tripError(error: unknown): TripOperationError {
  if (axios.isAxiosError(error) && error.response?.data && typeof error.response.data === 'object') {
    const data = error.response.data as Partial<TripOperationError>
    return { code: data.code || 'unknown', message: data.message || 'Request failed.', retryable: Boolean(data.retryable) }
  }
  return { code: 'network', message: 'The application is unreachable.', retryable: true }
}
