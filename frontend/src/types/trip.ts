export type Language = 'tr' | 'en'
export type Interest = 'culture' | 'nature' | 'food' | 'art'
export type Budget = 'economy' | 'balanced' | 'flexible'
export type Pace = 'relaxed' | 'balanced' | 'active'

export interface TripRequest {
  destination: string
  start_date: string
  end_date: string
  interests: Interest[]
  budget: Budget
  pace: Pace
  language: Language
  notes: string
}

export interface ValidatedTripRequest {
  request: TripRequest
  duration_days: number
  status: 'preferences_validated'
  itinerary_generated: false
}

export interface HealthResponse {
  status: 'ok'
  service: 'ai-travel-planner'
  version: string
  phase: number
}
