export interface AIStatus {
  gemini: {
    enabled: boolean
    reason: string
    model: string
    key_configured: boolean
    account_verification: 'unverified' | 'operator_attested'
    live_verified_this_process: boolean
    last_success_at: string | null
    policy_reviewed_at: string
  }
  research: Record<'google_maps' | 'google_search', { enabled: false; requested: boolean; reason: string }>
  itinerary_generation: false
  function_calling: false
}

export interface AIConnectionResult {
  mode: 'live'
  status: 'connected'
  model: string
  message: string
  checked_at: string
  itinerary_generated: false
  tool_calls_executed: 0
}
