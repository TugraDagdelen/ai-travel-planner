import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { TripsPage } from '../src/pages/TripsPage'
import { TripDetailPage } from '../src/pages/TripDetailPage'
import { deleteTrip, getTrip, listTrips, renameTrip, reviseTrip } from '../src/services/itinerary'
import type { TripRecord } from '../src/types/itinerary'

vi.mock('../src/components/ItineraryMap', () => ({ ItineraryMap: () => <div aria-label="Rota haritası">map</div> }))
vi.mock('../src/services/itinerary', () => ({ listTrips: vi.fn(), getTrip: vi.fn(), renameTrip: vi.fn(), deleteTrip: vi.fn(), reviseTrip: vi.fn(), tripError: () => ({ code: 'failed', message: 'failed', retryable: false }) }))

const trip: TripRecord = {
  id: 'trip-1', title: 'Paris planı', request: { destination: 'Paris', start_date: '2027-02-01', end_date: '2027-02-02', interests: ['culture'], budget: 'balanced', pace: 'relaxed', language: 'tr', notes: '' },
  destination: { id: 'demo:paris', name: 'Paris', country: 'France', country_code: 'FR', region: null, latitude: 48.85, longitude: 2.35, timezone: 'Europe/Paris', source_url: null }, generation_mode: 'demo', data_mode: 'demo',
  days: [{ date: '2027-02-01', weather: { date: '2027-02-01', available: true, reason: null, temperature_min: 8, temperature_max: 14, precipitation_mm: 0, precipitation_probability: 10, weather_code: 1 }, activities: [{ period: 'morning', place: { id: 'demo:museum', name: 'Demo Museum', category: 'museum', latitude: 48.85, longitude: 2.35, coordinate_kind: 'synthetic', distance_m: 100, indoor: 'indoor', classification_basis: 'synthetic', source_url: null }, reason: 'Kültür durağı' }], alternatives: [] }],
  sources: [{ mode: 'demo', source: 'Synthetic demo', source_url: null, fetched_at: null, cached: false }], warnings: [], agent_activity: [], revisions: [], version: 1, created_at: '2027-01-01T00:00:00Z', updated_at: '2027-01-01T00:00:00Z',
}

describe('saved trips', () => {
  beforeEach(() => { vi.mocked(listTrips).mockResolvedValue({ trips: [{ id: trip.id, title: trip.title, destination_name: 'Paris', start_date: '2027-02-01', end_date: '2027-02-02', generation_mode: 'demo', version: 1, updated_at: trip.updated_at }], total: 1 }); vi.mocked(getTrip).mockResolvedValue(trip); vi.mocked(renameTrip).mockResolvedValue({ ...trip, title: 'Paris hafta sonu', version: 2 }); vi.mocked(deleteTrip).mockResolvedValue(); vi.mocked(reviseTrip).mockResolvedValue({ ...trip, version: 2 }) })
  it('lists and links to a saved trip', async () => { render(<MemoryRouter><TripsPage language="tr"/></MemoryRouter>); expect(await screen.findByText('Paris planı')).toBeInTheDocument(); expect(screen.getByRole('link', { name: /Planı aç/ })).toHaveAttribute('href', '/trips/trip-1') })
  it('reopens, renames and deletes a trip through the UI', async () => { const user = userEvent.setup(); vi.spyOn(window, 'confirm').mockReturnValue(true); render(<MemoryRouter initialEntries={['/trips/trip-1']}><Routes><Route path="/trips/:id" element={<TripDetailPage language="tr"/>}/><Route path="/trips" element={<div>liste</div>}/></Routes></MemoryRouter>); expect(await screen.findByText('Paris planı')).toBeInTheDocument(); await user.click(screen.getByRole('button', { name: 'Başlığı düzenle' })); const input = screen.getByLabelText('Başlığı düzenle'); await user.clear(input); await user.type(input, 'Paris hafta sonu'); await user.click(screen.getByRole('button', { name: 'Başlığı kaydet' })); expect(renameTrip).toHaveBeenCalledWith('trip-1', 'Paris hafta sonu'); await user.click(screen.getByRole('button', { name: 'Seyahati sil' })); expect(deleteTrip).toHaveBeenCalledWith('trip-1'); expect(await screen.findByText('liste')).toBeInTheDocument() })
})
