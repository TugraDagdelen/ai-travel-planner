import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import App from '../src/App'
import { fetchHealth, validatePreferences } from '../src/services/api'
import type { TripRequest } from '../src/types/trip'
import { listTrips } from '../src/services/itinerary'

vi.mock('../src/services/api', () => ({ fetchHealth: vi.fn(), validatePreferences: vi.fn(), isConnectionError: () => true }))
vi.mock('../src/services/itinerary', () => ({ listTrips: vi.fn(), tripError: () => ({ code: 'network', message: 'offline', retryable: true }) }))

function renderApp(path = '/') {
  vi.mocked(fetchHealth).mockResolvedValue({ status: 'ok', service: 'ai-travel-planner', phase: 1, version: '0.1.0' })
  vi.mocked(listTrips).mockResolvedValue({ trips: [], total: 0 })
  return render(<MemoryRouter initialEntries={[path]}><App/></MemoryRouter>)
}

describe('travel preferences', () => {
  it('shows real backend status and switches the interface language', async () => {
    const user = userEvent.setup()
    renderApp()
    expect(await screen.findByText('Bağlantı hazır')).toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText('Dil seçimi'), 'en')
    expect(screen.getByText('Somewhere in mind?')).toBeInTheDocument()
    expect(document.documentElement.lang).toBe('en')
  })

  it('blocks invalid input without sending a request', async () => {
    const user = userEvent.setup()
    renderApp()
    await user.click(screen.getByRole('button', { name: 'Tercihlerimi gözden geçir' }))
    expect(screen.getByText('En az 2 karakterlik bir şehir adı yaz.')).toBeInTheDocument()
    expect(screen.getByText('En az bir ilgi alanı seç.')).toBeInTheDocument()
    expect(validatePreferences).not.toHaveBeenCalled()
  })

  it('validates through the API, opens a truthful summary, and keeps edits', async () => {
    const user = userEvent.setup()
    vi.mocked(validatePreferences).mockImplementation(async (request: TripRequest) => ({ request, duration_days: 4, status: 'preferences_validated', itinerary_generated: false }))
    renderApp()
    await user.type(screen.getByLabelText('Nereye gitmek istiyorsun?'), 'İstanbul, Türkiye')
    await user.type(screen.getByLabelText('Gidiş tarihi'), '2027-02-01')
    await user.type(screen.getByLabelText('Dönüş tarihi'), '2027-02-04')
    await user.click(screen.getByRole('button', { name: 'Tarih & kültür' }))
    await user.click(screen.getByRole('button', { name: 'Tercihlerimi gözden geçir' }))
    expect(await screen.findByText('Tercihlerin hazır.')).toBeInTheDocument()
    expect(screen.getByText('Planını oluştur')).toBeInTheDocument()
    expect(screen.getByText('İstanbul, Türkiye')).toBeInTheDocument()
    expect(validatePreferences).toHaveBeenCalledTimes(1)
    await user.click(screen.getByRole('link', { name: 'Tercihlerimi düzenle' }))
    expect(screen.getByLabelText('Nereye gitmek istiyorsun?')).toHaveValue('İstanbul, Türkiye')
  })

  it('shows failed health and recovers with retry', async () => {
    const user = userEvent.setup()
    renderApp()
    await screen.findByText('Bağlantı hazır')
    vi.mocked(fetchHealth).mockRejectedValueOnce(new Error('offline'))
    await user.click(screen.getByRole('button', { name: 'Yeniden dene' }))
    expect(await screen.findByText('Bağlantı kurulamadı')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Yeniden dene' }))
    await waitFor(() => expect(screen.getByText('Bağlantı hazır')).toBeInTheDocument())
  })

  it('shows the truthful empty state returned by saved-trip storage', async () => {
    renderApp('/trips')
    expect(await screen.findByText('Henüz kayıtlı bir seyahatin yok.')).toBeInTheDocument()
    expect(listTrips).toHaveBeenCalledTimes(1)
  })

  it('supports a direct planner URL with no in-memory preferences', () => {
    renderApp('/planner')
    expect(screen.getByText('Yolculuğuna bir başlangıç yap.')).toBeInTheDocument()
  })
})
