import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../src/App'
import { validatePreferences } from '../src/services/api'
import { fetchPlaces, fetchWeather, searchDestinations } from '../src/services/discovery'
import { deleteTrip, generateTrip, getTrip, listTrips, reviseTrip } from '../src/services/itinerary'
import type { Destination, Place } from '../src/types/discovery'
import type { TripRecord } from '../src/types/itinerary'
import type { TripRequest } from '../src/types/trip'

vi.mock('../src/components/ItineraryMap', () => ({ ItineraryMap: () => <div aria-label="Rota haritası">fixture map</div> }))
vi.mock('../src/services/api', () => ({ fetchHealth: vi.fn().mockResolvedValue({ status: 'ok', service: 'ai-travel-planner', phase: 6, version: '0.6.0' }), validatePreferences: vi.fn(), isConnectionError: () => false }))
vi.mock('../src/services/discovery', () => ({ searchDestinations: vi.fn(), fetchWeather: vi.fn(), fetchPlaces: vi.fn(), dataError: () => ({ code: 'provider_invalid_response', retryAfter: 0 }) }))
vi.mock('../src/services/itinerary', () => ({ generateTrip: vi.fn(), reviseTrip: vi.fn(), listTrips: vi.fn(), getTrip: vi.fn(), renameTrip: vi.fn(), deleteTrip: vi.fn(), tripError: () => ({ code: 'failed', message: 'failed', retryable: false }) }))

const destination: Destination = { id: 'demo:paris', name: 'Paris', country: 'France', country_code: 'FR', region: 'Île-de-France', latitude: 48.85, longitude: 2.35, timezone: 'Europe/Paris', source_url: null }
const places: Place[] = [
  { id: 'demo:historic', name: 'Demo · historic', category: 'historic', latitude: 48.85, longitude: 2.35, coordinate_kind: 'synthetic', distance_m: 100, indoor: 'unknown', classification_basis: 'synthetic', source_url: null },
  { id: 'demo:museum', name: 'Demo · museum', category: 'museum', latitude: 48.86, longitude: 2.36, coordinate_kind: 'synthetic', distance_m: 200, indoor: 'indoor', classification_basis: 'synthetic', source_url: null },
  { id: 'demo:restaurant', name: 'Demo · restaurant', category: 'restaurant', latitude: 48.87, longitude: 2.37, coordinate_kind: 'synthetic', distance_m: 300, indoor: 'indoor', classification_basis: 'synthetic', source_url: null },
]
const weatherDays = ['2027-02-01', '2027-02-02'].map(date => ({ date, available: true, reason: null, temperature_min: 7, temperature_max: 12, precipitation_mm: 1, precipitation_probability: 30, weather_code: 2 }))
const request: TripRequest = { destination: 'Paris, France', start_date: '2027-02-01', end_date: '2027-02-02', interests: ['culture', 'food'], budget: 'balanced', pace: 'relaxed', language: 'tr', notes: '' }
const trip: TripRecord = {
  id: 'trip-e2e', title: 'Paris · 2 gün', request, destination, generation_mode: 'demo', data_mode: 'demo',
  days: [{ date: weatherDays[0].date, weather: weatherDays[0], activities: [{ period: 'morning', place: places[0], reason: 'Doğrulanmış demo durağı.' }, { period: 'afternoon', place: places[1], reason: 'Doğrulanmış demo durağı.' }], alternatives: [] }, { date: weatherDays[1].date, weather: weatherDays[1], activities: [{ period: 'morning', place: places[2], reason: 'Doğrulanmış demo durağı.' }], alternatives: [] }],
  sources: [{ mode: 'demo', source: 'Synthetic demo', source_url: null, fetched_at: null, cached: false }], warnings: [], agent_activity: [], revisions: [], version: 1, created_at: '2027-01-31T00:00:00Z', updated_at: '2027-01-31T00:00:00Z',
}

describe('complete fixture-backed demo journey', () => {
  beforeEach(() => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(validatePreferences).mockImplementation(async value => ({ request: value, duration_days: 2, status: 'preferences_validated', itinerary_generated: false }))
    vi.mocked(searchDestinations).mockResolvedValue({ destinations: [destination], metadata: { mode: 'demo', source: 'Synthetic demo', source_url: null, fetched_at: null, cached: false } })
    vi.mocked(fetchWeather).mockResolvedValue({ destination_id: destination.id, timezone: destination.timezone, days: weatherDays, status: 'ok', units: { temperature: '°C', precipitation: 'mm', probability: '%' }, metadata: { mode: 'demo', source: 'Synthetic demo', source_url: null, fetched_at: null, cached: false } })
    vi.mocked(fetchPlaces).mockResolvedValue({ destination_id: destination.id, places, radius_m: 1500, result_limit: 40, truncated: false, skipped_records: 0, metadata: { mode: 'demo', source: 'Synthetic demo', source_url: null, fetched_at: null, cached: false } })
    vi.mocked(generateTrip).mockResolvedValue(trip)
    vi.mocked(getTrip).mockResolvedValue(trip)
    vi.mocked(reviseTrip).mockResolvedValue({ ...trip, version: 2, revisions: [{ instruction: '2. günü değiştir', result_summary: '2. günün ilk durağı güncellendi.', version: 2, created_at: '2027-01-31T01:00:00Z' }] })
    vi.mocked(deleteTrip).mockResolvedValue()
    vi.mocked(listTrips).mockResolvedValue({ trips: [], total: 0 })
  })

  it('creates, reopens, revises and deletes a demo trip through the real screens', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter><App/></MemoryRouter>)
    await user.type(screen.getByLabelText('Nereye gitmek istiyorsun?'), request.destination)
    await user.type(screen.getByLabelText('Gidiş tarihi'), request.start_date)
    await user.type(screen.getByLabelText('Dönüş tarihi'), request.end_date)
    await user.click(screen.getByRole('button', { name: 'Tarih & kültür' }))
    await user.click(screen.getByRole('button', { name: 'Yerel lezzetler' }))
    await user.click(screen.getByRole('button', { name: 'Tercihlerimi gözden geçir' }))
    expect(await screen.findByText('Tercihlerin hazır.')).toBeInTheDocument()

    await user.selectOptions(screen.getByLabelText('Veri modu'), 'demo')
    await user.click(screen.getByRole('button', { name: 'Şehri bul' }))
    await user.click(await screen.findByRole('button', { name: /Paris.*France.*FR/ }))
    await user.click(await screen.findByRole('button', { name: 'Planı oluştur ve kaydet' }))
    expect(await screen.findByRole('heading', { name: trip.title })).toBeInTheDocument()
    expect(generateTrip).toHaveBeenCalledWith(expect.objectContaining({ generation_mode: 'demo', idempotency_key: expect.any(String) }))

    await user.click(screen.getByRole('link', { name: 'Kayıtlı planı aç' }))
    expect(await screen.findByRole('button', { name: 'Seyahati sil' })).toBeInTheDocument()
    await user.type(screen.getByLabelText('Değişiklik isteğini yaz'), '2. günü değiştir')
    await user.click(screen.getByRole('button', { name: 'Değişikliği uygula' }))
    expect(await screen.findByText('2. günün ilk durağı güncellendi.')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Seyahati sil' }))
    expect(deleteTrip).toHaveBeenCalledWith(trip.id)
    expect(await screen.findByText('Henüz kayıtlı bir seyahatin yok.')).toBeInTheDocument()
  })
})
