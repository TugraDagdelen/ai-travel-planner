import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ItineraryView } from '../src/components/ItineraryView'
import type { Place } from '../src/types/discovery'
import type { TripRecord } from '../src/types/itinerary'

vi.mock('../src/components/ItineraryMap', () => ({
  ItineraryMap: ({ places, activeId, onSelect }: { places: Place[]; activeId: string | null; onSelect: (id: string) => void }) => <div data-testid="route-map" data-active={activeId}><button onClick={() => onSelect(places[1]?.id ?? places[0].id)}>map-select-second</button></div>,
}))

const liveMuseum: Place = { id: 'osm:node:1', name: 'Live Museum', category: 'museum', latitude: 41.01, longitude: 28.97, coordinate_kind: 'node', distance_m: 100, indoor: 'indoor', classification_basis: 'osm_tag', source_url: 'https://www.openstreetmap.org/node/1' }
const livePark: Place = { id: 'osm:way:2', name: 'Live Park', category: 'park', latitude: 41.02, longitude: 28.98, coordinate_kind: 'geometry_center', distance_m: 300, indoor: 'outdoor', classification_basis: 'osm_tag', source_url: 'https://www.openstreetmap.org/way/2' }
const liveRestaurant: Place = { id: 'wikidata:3', name: 'Live Restaurant', category: 'restaurant', latitude: 41.03, longitude: 28.99, coordinate_kind: 'node', distance_m: 450, indoor: 'unknown', classification_basis: 'category_inference', source_url: 'https://en.wikipedia.org/wiki/Live_Restaurant', description: 'A notable local restaurant.', pageviews_30d: 2500 }

const trip: TripRecord = {
  id: 'trip-live', title: 'İstanbul kültür rotası', request: { destination: 'İstanbul', start_date: '2027-02-01', end_date: '2027-02-01', interests: ['culture'], budget: 'economy', pace: 'relaxed', language: 'tr', notes: '' },
  destination: { id: 'geonames:745044', name: 'İstanbul', country: 'Türkiye', country_code: 'TR', region: null, latitude: 41.01, longitude: 28.97, timezone: 'Europe/Istanbul', source_url: 'https://www.openstreetmap.org/' }, generation_mode: 'deterministic', data_mode: 'live',
  days: [{ date: '2027-02-01', weather: { date: '2027-02-01', available: true, reason: null, temperature_min: 7, temperature_max: 12, precipitation_mm: 3, precipitation_probability: 70, weather_code: 61 }, activities: [{ period: 'morning', place: liveMuseum, reason: 'Yağmurlu sabah için iç mekân.' }, { period: 'afternoon', place: livePark, reason: 'Kaynağı doğrulanmış yakın park.' }], alternatives: [liveMuseum] }],
  sources: [{ mode: 'live', source: '© OpenStreetMap contributors', source_url: 'https://www.openstreetmap.org/copyright', fetched_at: '2027-01-31T00:00:00Z', cached: false }], warnings: [], agent_activity: [], revisions: [], version: 1, created_at: '2027-01-31T00:00:00Z', updated_at: '2027-01-31T00:00:00Z',
}

describe('ItineraryView map and evidence links', () => {
  it('keeps map and timeline selection synchronized and exposes citations', async () => {
    const user = userEvent.setup()
    render(<ItineraryView trip={trip} language="tr"/>)
    expect(await screen.findByTestId('route-map')).toHaveAttribute('data-active', liveMuseum.id)
    expect(screen.getByRole('button', { name: /Live Museum/ })).toHaveAttribute('aria-pressed', 'true')
    await user.click(screen.getByRole('button', { name: /Live Park/ }))
    expect(screen.getByTestId('route-map')).toHaveAttribute('data-active', livePark.id)
    expect(screen.getByRole('button', { name: /Live Park/ })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getAllByRole('link', { name: /Kaynağı aç/ }).length).toBeGreaterThan(0)
    expect(screen.getAllByRole('link', { name: /Google Maps ile yol tarifi/ })[0]).toHaveAttribute('href', expect.stringContaining('destination=41.01,28.97'))
  })

  it('does not create navigation links for synthetic demo coordinates', async () => {
    const demoPlace: Place = { ...liveMuseum, id: 'demo:museum', name: 'Demo Museum', coordinate_kind: 'synthetic', classification_basis: 'synthetic', source_url: null }
    const demoTrip: TripRecord = { ...trip, id: 'trip-demo', generation_mode: 'demo', data_mode: 'demo', days: [{ ...trip.days[0], activities: [{ ...trip.days[0].activities[0], place: demoPlace }], alternatives: [] }], sources: [{ mode: 'demo', source: 'Synthetic demo', source_url: null, fetched_at: null, cached: false }] }
    render(<ItineraryView trip={demoTrip} language="tr"/>)
    expect(await screen.findByText(/Sentetik demo konumu/)).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Google Maps ile yol tarifi/ })).not.toBeInTheDocument()
  })

  it('separates daily visits from food and shows rich source context', async () => {
    const foodTrip: TripRecord = { ...trip, request: { ...trip.request, interests: ['culture', 'food'] }, days: [{ ...trip.days[0], activities: [...trip.days[0].activities, { period: 'evening', place: liveRestaurant, reason: 'Akşam yemeği.' }] }] }
    render(<ItineraryView trip={foodTrip} language="tr"/>)
    expect(await screen.findByRole('heading', { name: 'Gezilecek yerler' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Yemek' })).toBeInTheDocument()
    expect(screen.getByText('A notable local restaurant.')).toBeInTheDocument()
    expect(screen.getByText(/2\.500 · 30 günlük Wikipedia ilgisi/)).toBeInTheDocument()
  })
})
