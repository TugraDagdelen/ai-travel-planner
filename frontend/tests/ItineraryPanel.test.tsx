import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { ItineraryPanel } from '../src/components/ItineraryPanel'
import { generateTrip, reviseTrip } from '../src/services/itinerary'
import type { TripRecord } from '../src/types/itinerary'
import type { TripRequest } from '../src/types/trip'

vi.mock('../src/services/itinerary', () => ({
  generateTrip: vi.fn(),
  reviseTrip: vi.fn(),
  tripError: () => ({ code: 'unknown', message: 'failed', retryable: false }),
}))
vi.mock('../src/components/ItineraryMap', () => ({ ItineraryMap: () => <div>map</div> }))

const request: TripRequest = {
  destination: 'Paris, France', start_date: '2027-02-01', end_date: '2027-02-02',
  interests: ['culture', 'food'], budget: 'balanced',
  pace: 'relaxed', language: 'tr', notes: '',
}
const destination = {
  id: 'demo:paris', name: 'Paris', country: 'France', country_code: 'FR', region: null,
  latitude: 48.85, longitude: 2.35, timezone: 'Europe/Paris', source_url: null,
}
const place = {
  id: 'demo:museum', name: 'Demo Museum', category: 'museum' as const,
  latitude: 48.85, longitude: 2.35, coordinate_kind: 'synthetic' as const,
  distance_m: 120, indoor: 'unknown' as const, classification_basis: 'synthetic' as const,
  source_url: null,
}
const trip: TripRecord = {
  id: 'trip-1', title: 'Paris · 2 gün', request, destination, generation_mode: 'demo' as const,
  data_mode: 'demo' as const, version: 1, created_at: '2027-01-01T00:00:00Z', updated_at: '2027-01-01T00:00:00Z',
  warnings: [], revisions: [], sources: [{ mode: 'demo' as const, source: 'Synthetic demo', source_url: null, fetched_at: null, cached: false }],
  agent_activity: [{ kind: 'tool' as const, name: 'get_weather', status: 'success' as const, duration_ms: 1, cached: false, summary: '2 weather days' }],
  days: [{
    date: '2027-02-01',
    weather: { date: '2027-02-01', available: true, reason: null, temperature_min: 10, temperature_max: 15, precipitation_mm: 0, precipitation_probability: 10, weather_code: 1 },
    activities: [{ period: 'morning' as const, place, reason: 'Verified place' }], alternatives: [],
  }],
}

describe('ItineraryPanel', () => {
  beforeEach(() => vi.clearAllMocks())

  it('requires a city selection', () => {
    render(<ItineraryPanel request={request} language="tr" selection={null}/>)
    expect(screen.getByText('Önce yukarıdan doğru şehri seç.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Planı oluştur ve kaydet' })).not.toBeInTheDocument()
  })

  it('generates a labelled demo plan and revises the saved record', async () => {
    vi.mocked(generateTrip).mockResolvedValue(trip)
    vi.mocked(reviseTrip).mockResolvedValue({ ...trip, version: 2, revisions: [{ instruction: 'İlk iki durağı değiştir', result_summary: 'İlk iki durak yer değiştirdi.', version: 2, created_at: '2027-01-01T01:00:00Z' }] })
    const user = userEvent.setup()
    render(<MemoryRouter><ItineraryPanel request={request} language="tr" selection={{ destination, mode: 'demo' }}/></MemoryRouter>)
    await user.click(screen.getByRole('button', { name: 'Planı oluştur ve kaydet' }))
    expect(await screen.findByText('Paris · 2 gün')).toBeInTheDocument()
    expect(screen.getByText('Demo')).toBeInTheDocument()
    expect(generateTrip).toHaveBeenCalledWith(expect.objectContaining({ generation_mode: 'demo' }))
    await user.type(screen.getByLabelText('Değişiklik isteğini yaz'), 'İlk iki durağı değiştir')
    await user.click(screen.getByRole('button', { name: 'Değişikliği uygula' }))
    expect(reviseTrip).toHaveBeenCalledWith('trip-1', 'İlk iki durağı değiştir')
    expect(await screen.findAllByText(/Sürüm 2/)).not.toHaveLength(0)
  })
})
