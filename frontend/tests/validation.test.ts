import { describe, expect, it } from 'vitest'
import { validateDraft } from '../src/services/validation'
import type { TripRequest } from '../src/types/trip'

const draft: TripRequest = { destination: 'Barcelona', start_date: '2027-01-01', end_date: '2027-01-14', interests: ['culture'], budget: 'balanced', pace: 'relaxed', language: 'en', notes: '' }

describe('inclusive trip duration validation', () => {
  it('accepts exactly 14 days and one-day trips', () => {
    expect(validateDraft(draft)).toEqual({})
    expect(validateDraft({ ...draft, end_date: draft.start_date })).toEqual({})
  })
  it('rejects 15 days, reversed dates and missing dates', () => {
    expect(validateDraft({ ...draft, end_date: '2027-01-15' })).toEqual({ dates: 'durationError' })
    expect(validateDraft({ ...draft, end_date: '2026-12-31' })).toEqual({ dates: 'dateError' })
    expect(validateDraft({ ...draft, start_date: '' })).toEqual({ dates: 'dateError' })
  })
})
