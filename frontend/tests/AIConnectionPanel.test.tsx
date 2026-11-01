import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AIConnectionPanel } from '../src/components/AIConnectionPanel'
import { checkAIConnection, fetchAIStatus } from '../src/services/ai'
import type { AIStatus } from '../src/types/ai'

vi.mock('../src/services/ai', () => ({ checkAIConnection: vi.fn(), fetchAIStatus: vi.fn() }))

const ready: AIStatus = {
  gemini: { enabled: true, reason: 'ready_to_check', model: 'gemini-3.5-flash-lite', key_configured: true, account_verification: 'operator_attested', live_verified_this_process: false, last_success_at: null, policy_reviewed_at: '2026-10-30' },
  research: { google_maps: { enabled: false, requested: false, reason: 'disabled_by_configuration' }, google_search: { enabled: false, requested: false, reason: 'disabled_by_configuration' } },
  itinerary_generation: false, function_calling: false,
}

describe('AI connection panel', () => {
  it('checks status explicitly without sending a model request', async () => {
    const user = userEvent.setup()
    vi.mocked(fetchAIStatus).mockResolvedValue({ ...ready, gemini: { ...ready.gemini, enabled: false, reason: 'missing_api_key', key_configured: false } })
    render(<AIConnectionPanel language="tr"/>)
    expect(fetchAIStatus).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Durumu kontrol et' }))
    expect(await screen.findByText('Gemini anahtarı henüz eklenmemiş.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Gemini bağlantısını dene' })).not.toBeInTheDocument()
    expect(checkAIConnection).not.toHaveBeenCalled()
  })

  it('sends only language after the user starts the test and displays the real response', async () => {
    const user = userEvent.setup()
    vi.mocked(fetchAIStatus).mockResolvedValue(ready)
    vi.mocked(checkAIConnection).mockResolvedValue({ mode: 'live', status: 'connected', model: ready.gemini.model, message: 'Hello from the test', checked_at: '2026-10-30T00:00:00Z', itinerary_generated: false, tool_calls_executed: 0 })
    render(<AIConnectionPanel language="en"/>)
    await user.click(screen.getByRole('button', { name: 'Check status' }))
    expect(checkAIConnection).not.toHaveBeenCalled()
    await user.click(await screen.findByRole('button', { name: 'Test Gemini connection' }))
    expect(await screen.findByText('Gemini responded.')).toBeInTheDocument()
    expect(screen.getByText('Hello from the test')).toBeInTheDocument()
    expect(checkAIConnection).toHaveBeenCalledExactlyOnceWith('en', expect.any(AbortSignal))
    expect(screen.getByText(/tool-using planner is ready/)).toBeInTheDocument()
  })

  it('shows quota errors, disables retries during cooldown and never fabricates success', async () => {
    const user = userEvent.setup()
    vi.mocked(fetchAIStatus).mockResolvedValue(ready)
    vi.mocked(checkAIConnection).mockRejectedValue({ isAxiosError: true, response: { data: { code: 'ai_quota_exhausted', retry_after_seconds: 120 } } })
    render(<AIConnectionPanel language="en"/>)
    await user.click(screen.getByRole('button', { name: 'Check status' }))
    await user.click(await screen.findByRole('button', { name: 'Test Gemini connection' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('usage limit')
    expect(screen.getByRole('button', { name: 'Test Gemini connection' })).toBeDisabled()
    expect(screen.queryByText('Gemini responded.')).not.toBeInTheDocument()
  })

  it('keeps setup visible when free eligibility is unconfirmed and supports language changes', async () => {
    const user = userEvent.setup()
    vi.mocked(fetchAIStatus).mockResolvedValue({ ...ready, gemini: { ...ready.gemini, enabled: false, reason: 'free_tier_unconfirmed' } })
    const view = render(<AIConnectionPanel language="tr"/>)
    await user.click(screen.getByRole('button', { name: 'Durumu kontrol et' }))
    expect(await screen.findByText('Hesabın ücretsiz kullanım durumu henüz kontrol edilmemiş.')).toBeInTheDocument()
    view.rerender(<AIConnectionPanel language="en"/>)
    expect(screen.getByText('Free-tier account eligibility has not been checked yet.')).toBeInTheDocument()
    expect(checkAIConnection).not.toHaveBeenCalled()
  })

  it('disables duplicate clicks and aborts an in-flight check on unmount', async () => {
    const user = userEvent.setup()
    vi.mocked(fetchAIStatus).mockResolvedValue(ready)
    vi.mocked(checkAIConnection).mockImplementation(() => new Promise(() => {}))
    const view = render(<AIConnectionPanel language="en"/>)
    await user.click(screen.getByRole('button', { name: 'Check status' }))
    const button = await screen.findByRole('button', { name: 'Test Gemini connection' })
    await user.click(button)
    await user.click(button)
    await waitFor(() => expect(checkAIConnection).toHaveBeenCalledTimes(1))
    const signal = vi.mocked(checkAIConnection).mock.calls[0][1]
    view.unmount()
    expect(signal.aborted).toBe(true)
  })
})
