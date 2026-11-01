import { beforeEach, describe, expect, it, vi } from 'vitest'
import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DiscoveryPanel } from '../src/components/DiscoveryPanel'
import { fetchPlaces, fetchWeather, searchDestinations } from '../src/services/discovery'
import type { DestinationResponse, SourceMetadata, WeatherResponse } from '../src/types/discovery'
import type { TripRequest } from '../src/types/trip'

vi.mock('../src/services/discovery', () => ({ searchDestinations: vi.fn(), fetchWeather: vi.fn(), fetchPlaces: vi.fn(), dataError: () => ({ code: 'provider_timeout', retryAfter: 0 }) }))

const request: TripRequest = { destination: 'Paris, France', start_date: '2027-02-01', end_date: '2027-02-02', interests: ['culture'], budget: 'balanced', pace: 'relaxed', language: 'en', notes: 'Private note' }
const metadata: SourceMetadata = { mode: 'live', source: 'Open-Meteo', source_url: 'https://open-meteo.com/', fetched_at: '2027-02-01T08:00:00Z', cached: false }
const cities: DestinationResponse = {
  destinations: [
    { id: 'geonames:1', name: 'Paris', region: 'Île-de-France', country: 'France', country_code: 'FR', latitude: 48.85, longitude: 2.35, timezone: 'Europe/Paris', source_url: null },
    { id: 'geonames:2', name: 'Paris', region: 'Texas', country: 'United States', country_code: 'US', latitude: 33.66, longitude: -95.55, timezone: 'America/Chicago', source_url: null },
  ], metadata,
}
const weather: WeatherResponse = {
  destination_id: 'geonames:1', timezone: 'Europe/Paris', status: 'partial', metadata,
  units: { temperature: '°C', precipitation: 'mm', probability: '%' },
  days: [
    { date: '2027-02-01', available: true, reason: null, temperature_min: 8, temperature_max: 14, precipitation_mm: 2, precipitation_probability: 60, weather_code: 61 },
    { date: '2027-02-02', available: false, reason: 'outside_forecast_horizon', temperature_min: null, temperature_max: null, precipitation_mm: null, precipitation_probability: null, weather_code: null },
  ],
}

beforeEach(() => {
  vi.mocked(searchDestinations).mockReset().mockResolvedValue(cities)
  vi.mocked(fetchWeather).mockReset().mockResolvedValue(weather)
  vi.mocked(fetchPlaces).mockReset().mockResolvedValue({ destination_id: 'geonames:1', radius_m: 1500, result_limit: 40, truncated: false, skipped_records: 0, metadata: { ...metadata, source: '© OpenStreetMap contributors', source_url: 'https://www.openstreetmap.org/copyright' }, places: [{ id: 'fixture:1', name: 'Fixture Museum', category: 'museum', latitude: null, longitude: null, coordinate_kind: 'unknown', distance_m: null, indoor: 'indoor', classification_basis: 'category_inference', source_url: null }] })
})

async function chooseCity() {
  const user = userEvent.setup()
  await user.click(screen.getByRole('button', { name: 'Find city' }))
  await user.click(await screen.findByRole('button', { name: /Paris Île-de-France/ }))
  return user
}

describe('real data discovery', () => {
  it('requires explicit city selection and sends neither personal notes nor guessed coordinates', async () => {
    const user = userEvent.setup()
    render(<DiscoveryPanel request={request} language="en" />)
    expect(searchDestinations).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Find city' }))
    expect(await screen.findByRole('button', { name: /Paris Texas/ })).toBeInTheDocument()
    expect(fetchWeather).not.toHaveBeenCalled()
    expect(searchDestinations).toHaveBeenCalledWith('Paris', '', 'en', 'live', expect.any(AbortSignal))
    await user.click(screen.getByRole('button', { name: /Paris Île-de-France/ }))
    expect(await screen.findByText('Fixture Museum')).toBeInTheDocument()
    expect(fetchWeather).toHaveBeenCalledWith('geonames:1', '2027-02-01', '2027-02-02', 'live', expect.any(AbortSignal))
    expect(screen.getByText('No forecast is available for this date.')).toBeInTheDocument()
    expect(screen.getByText('No verifiable coordinates')).toBeInTheDocument()
    expect(screen.getByText(/Inferred from category/)).toBeInTheDocument()
  })

  it('keeps place results when the weather service fails', async () => {
    vi.mocked(fetchWeather).mockRejectedValue(new Error('timeout'))
    render(<DiscoveryPanel request={request} language="en" />)
    await chooseCity()
    expect(await screen.findByText(/did not respond in time/)).toBeInTheDocument()
    expect(screen.getByText('Fixture Museum')).toBeInTheDocument()
  })

  it('labels demo mode and passes it explicitly instead of silently replacing live data', async () => {
    const user = userEvent.setup()
    render(<DiscoveryPanel request={request} language="en" />)
    await user.selectOptions(screen.getByLabelText('Data mode'), 'demo')
    expect(screen.getByText(/DEMO · Weather and places are synthetic/)).toBeInTheDocument()
    expect(searchDestinations).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Find city' }))
    expect(await screen.findByRole('button', { name: /Paris Île-de-France/ })).toBeInTheDocument()
    expect(searchDestinations).toHaveBeenCalledWith('Paris', '', 'en', 'demo', expect.any(AbortSignal))
  })

  it('discards an old response after switching modes', async () => {
    let resolveWeather!: (value: WeatherResponse) => void
    vi.mocked(fetchWeather).mockReturnValue(new Promise(resolve => { resolveWeather = resolve }))
    render(<DiscoveryPanel request={request} language="en" />)
    const user = await chooseCity()
    await user.selectOptions(screen.getByLabelText('Data mode'), 'demo')
    await act(async () => resolveWeather(weather))
    expect(screen.queryByText('Weather for your dates')).not.toBeInTheDocument()
    expect(screen.queryByText('Fixture Museum')).not.toBeInTheDocument()
  })

  it('provides a localized no-results state', async () => {
    vi.mocked(searchDestinations).mockResolvedValue({ destinations: [], metadata })
    const user = userEvent.setup()
    render(<DiscoveryPanel request={request} language="tr" />)
    await user.click(screen.getByRole('button', { name: 'Şehri bul' }))
    expect(await screen.findByText(/Eşleşen şehir bulunamadı/)).toBeInTheDocument()
    expect(fetchPlaces).not.toHaveBeenCalled()
  })
})
