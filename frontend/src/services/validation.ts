import type { TripRequest } from '../types/trip'

export type ValidationErrors = Partial<Record<'destination' | 'dates' | 'interests' | 'notes', 'destinationError' | 'dateError' | 'durationError' | 'interestsError' | 'notesError'>>

export function validateDraft(draft: TripRequest): ValidationErrors {
  const errors: ValidationErrors = {}
  if (draft.destination.trim().length < 2 || draft.destination.length > 120) errors.destination = 'destinationError'
  const start = Date.parse(draft.start_date)
  const end = Date.parse(draft.end_date)
  if (!draft.start_date || !draft.end_date || !Number.isFinite(start) || !Number.isFinite(end) || end < start) {
    errors.dates = 'dateError'
  } else if ((end - start) / 86400000 + 1 > 14) {
    errors.dates = 'durationError'
  }
  if (!draft.interests.length) errors.interests = 'interestsError'
  if (draft.notes.length > 1000) errors.notes = 'notesError'
  return errors
}
