import { useRef, useState } from 'react'
import { Bot, ExternalLink, RefreshCw, Route } from 'lucide-react'
import { Link } from 'react-router-dom'
import { itineraryCopy } from '../i18n/itinerary'
import { generateTrip, tripError } from '../services/itinerary'
import type { DataMode, Destination } from '../types/discovery'
import type { GenerationMode, TripRecord } from '../types/itinerary'
import type { Language, TripRequest } from '../types/trip'
import { ItineraryView } from './ItineraryView'
import { RevisionPanel } from './RevisionPanel'

export interface DestinationSelection { destination: Destination; mode: DataMode }

export function ItineraryPanel({ request, language, selection }: { request: TripRequest; language: Language; selection: DestinationSelection | null }) {
  const t = itineraryCopy[language]
  const [mode, setMode] = useState<GenerationMode>(selection?.mode === 'demo' ? 'demo' : 'deterministic')
  const [trip, setTrip] = useState<TripRecord | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const idempotencyKey = useRef(crypto.randomUUID())
  const hint = mode === 'ai' ? t.aiHint : mode === 'demo' ? t.demoHint : t.deterministicHint
  function message(code: string, fallback: string) {
    if (['missing_api_key', 'free_tier_unconfirmed', 'model_not_reviewed'].includes(code)) return t.missingKey
    if (code === 'insufficient_place_evidence') return t.insufficient
    if (['provider_timeout', 'provider_unavailable', 'provider_rate_limited', 'local_request_limit'].includes(code)) return t.placeSourceUnavailable
    if (['ai_timeout', 'ai_provider_unavailable', 'ai_quota_exhausted', 'ai_local_limit', 'ai_busy'].includes(code)) return t.aiUnavailable
    return fallback || t.failed
  }
  async function create() { if (!selection) return; setLoading(true); setError(''); try { setTrip(await generateTrip({ request, destination_id: selection.destination.id, data_mode: selection.mode, generation_mode: mode, idempotency_key: idempotencyKey.current })) } catch (cause) { const problem = tripError(cause); setError(message(problem.code, problem.message)) } finally { setLoading(false) } }
  return <section className="itinerary-panel" aria-label={t.title}>
    <span className="tiny-eyebrow">{t.eyebrow}</span><h2><Route size={25}/>{t.title}</h2><p>{t.intro}</p>
    {!selection ? <p className="itinerary-prompt">{t.choose}</p> : !trip && <><div className="mode-select itinerary-mode"><label htmlFor="generation-mode">{t.mode}</label><select id="generation-mode" value={mode} disabled={loading} onChange={event => setMode(event.target.value as GenerationMode)}>{selection.mode === 'demo' ? <option value="demo">{t.demo}</option> : <><option value="deterministic">{t.deterministic}</option><option value="ai">{t.ai}</option></>}</select></div><p className="generation-hint">{hint}</p>{mode === 'ai' && <p className="privacy-hint"><Bot size={16}/>{t.privacy}</p>}<button type="button" className="primary-button" onClick={() => void create()} disabled={loading}>{loading ? <RefreshCw className="spin" size={16}/> : <Route size={16}/>} {loading ? t.generating : t.generate}</button></>}
    {error && <div className="data-error" role="alert"><p>{t.failed}</p><p>{error}</p></div>}
    {trip && <><div className="saved-actions"><Link to={`/trips/${trip.id}`}>{language === 'tr' ? 'Kayıtlı planı aç' : 'Open saved plan'}<ExternalLink size={14}/></Link></div><ItineraryView trip={trip} language={language}/><RevisionPanel trip={trip} language={language} onChange={setTrip}/></>}
  </section>
}
