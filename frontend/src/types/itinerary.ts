import type { DataMode, Destination, Place, SourceMetadata, WeatherDay } from './discovery'
import type { TripRequest } from './trip'

export type GenerationMode = 'ai' | 'deterministic' | 'demo'

export interface ItineraryActivity {
  period: 'morning' | 'afternoon' | 'evening'
  place: Place
  reason: string
}

export interface ItineraryDay {
  date: string
  weather: WeatherDay
  activities: ItineraryActivity[]
  alternatives: Place[]
}

export interface AgentActivity {
  kind: 'tool' | 'model' | 'validation' | 'storage' | 'reuse'
  name: string
  status: 'success' | 'partial' | 'failed' | 'reused'
  duration_ms: number
  cached: boolean
  summary: string
}

export interface RevisionEntry {
  instruction: string
  result_summary: string
  version: number
  created_at: string
}

export interface TripRecord {
  id: string
  title: string
  request: TripRequest
  destination: Destination
  generation_mode: GenerationMode
  data_mode: DataMode
  days: ItineraryDay[]
  sources: SourceMetadata[]
  warnings: string[]
  agent_activity: AgentActivity[]
  revisions: RevisionEntry[]
  version: number
  created_at: string
  updated_at: string
}

export interface GenerateTripRequest {
  request: TripRequest
  destination_id: string
  data_mode: DataMode
  generation_mode: GenerationMode
  idempotency_key: string
}

export interface TripSummary {
  id: string
  title: string
  destination_name: string
  start_date: string
  end_date: string
  generation_mode: GenerationMode
  version: number
  updated_at: string
}

export interface TripList { trips: TripSummary[]; total: number }
