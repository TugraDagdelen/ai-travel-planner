import { useState } from 'react'
import { MessageCircle, RefreshCw } from 'lucide-react'
import { tripsCopy } from '../i18n/trips'
import { reviseTrip, tripError } from '../services/itinerary'
import type { TripRecord } from '../types/itinerary'
import type { Language } from '../types/trip'

export function RevisionPanel({ trip, language, onChange }: { trip: TripRecord; language: Language; onChange: (trip: TripRecord) => void }) {
  const t = tripsCopy[language]
  const [instruction, setInstruction] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  async function submit() { if (instruction.trim().length < 3) return; setLoading(true); setError(''); try { onChange(await reviseTrip(trip.id, instruction.trim())); setInstruction('') } catch (cause) { setError(tripError(cause).message || t.operationFailed) } finally { setLoading(false) } }
  return <section className="revision-panel" aria-labelledby="revision-title"><div className="section-title"><MessageCircle size={20}/><h2 id="revision-title">{t.revise}</h2></div><p>{t.reviseHint}</p>
    <div className="revision-history" aria-label={t.revisionHistory}>{trip.revisions.length === 0 ? <span className="empty-revisions">{t.noRevisions}</span> : trip.revisions.map(entry => <div className="revision-pair" key={`${entry.version}-${entry.created_at}`}><p><strong>{t.you}</strong>{entry.instruction}</p><p><strong>{t.assistant} · {t.version} {entry.version}</strong>{entry.result_summary}</p></div>)}</div>
    <label htmlFor="revision">{t.revisePlaceholder}</label><textarea id="revision" value={instruction} maxLength={500} onChange={event => setInstruction(event.target.value)} placeholder={t.revisePlaceholder}/>{error && <p className="inline-error" role="alert">{error}</p>}<button type="button" className="primary-button" disabled={loading || instruction.trim().length < 3} onClick={() => void submit()}>{loading ? <RefreshCw className="spin" size={16}/> : <MessageCircle size={16}/>} {loading ? t.revising : t.send}</button>
  </section>
}
