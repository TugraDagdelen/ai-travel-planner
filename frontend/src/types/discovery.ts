export type DataMode = 'live' | 'demo'
export type Category = 'museum' | 'historic' | 'park' | 'attraction' | 'restaurant'

export interface SourceMetadata {
  mode: DataMode
  source: string
  source_url: string | null
  fetched_at: string | null
  cached: boolean
}

export interface Destination {
  id: string
  name: string
  country: string
  country_code: string
  region: string | null
  latitude: number
  longitude: number
  timezone: string
  source_url: string | null
}

export interface DestinationResponse { destinations: Destination[]; metadata: SourceMetadata }

export interface WeatherDay {
  date: string
  available: boolean
  reason: 'outside_forecast_horizon' | 'missing_data' | null
  temperature_min: number | null
  temperature_max: number | null
  precipitation_mm: number | null
  precipitation_probability: number | null
  weather_code: number | null
}

export interface WeatherResponse {
  destination_id: string
  timezone: string
  days: WeatherDay[]
  status: 'ok' | 'partial' | 'unavailable'
  units: { temperature: string; precipitation: string; probability: string }
  metadata: SourceMetadata
}

export interface Place {
  id: string
  name: string
  category: Category
  latitude: number | null
  longitude: number | null
  coordinate_kind: 'node' | 'geometry_center' | 'unknown' | 'synthetic'
  distance_m: number | null
  indoor: 'indoor' | 'outdoor' | 'unknown'
  classification_basis: 'osm_tag' | 'category_inference' | 'unknown' | 'synthetic'
  source_url: string | null
}

export interface PlacesResponse {
  destination_id: string
  places: Place[]
  radius_m: number
  result_limit: number
  truncated: boolean
  skipped_records: number
  metadata: SourceMetadata
}
