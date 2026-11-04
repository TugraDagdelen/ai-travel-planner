import { useEffect, useState } from 'react'
import { ArrowLeft, Edit3, RefreshCw, Save, Trash2, X } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { deleteTrip, getTrip, renameTrip, tripError } from '../services/itinerary'
import { tripsCopy } from '../i18n/trips'
import type { TripRecord } from '../types/itinerary'
import type { Language } from '../types/trip'
import { ItineraryView } from '../components/ItineraryView'
import { RevisionPanel } from '../components/RevisionPanel'
import { PlanEditor } from '../components/PlanEditor'

export function TripDetailPage({ language }: { language: Language }) {
  const t = tripsCopy[language], { id = '' } = useParams(), navigate = useNavigate()
  const [trip, setTrip] = useState<TripRecord | null>(null), [loading, setLoading] = useState(true), [error, setError] = useState(''), [editing, setEditing] = useState(false), [title, setTitle] = useState(''), [busy, setBusy] = useState(false)
  useEffect(() => { let active = true; getTrip(id).then(value => { if (active) { setTrip(value); setTitle(value.title) } }).catch(cause => { if (active) setError(tripError(cause).message) }).finally(() => { if (active) setLoading(false) }); return () => { active = false } }, [id])
  async function save() { if (!trip || title.trim().length < 2) return; setBusy(true); setError(''); try { const value = await renameTrip(trip.id, title.trim()); setTrip(value); setEditing(false) } catch (cause) { setError(tripError(cause).message) } finally { setBusy(false) } }
  async function remove() { if (!trip || !window.confirm(t.deleteConfirm)) return; setBusy(true); try { await deleteTrip(trip.id); navigate('/trips', { replace: true }) } catch (cause) { setError(tripError(cause).message); setBusy(false) } }
  if (loading) return <div className="page-state" role="status"><RefreshCw className="spin"/>{t.loading}</div>
  if (!trip) return <div className="empty-trip-list"><h1>{t.notFound}</h1><p>{error || t.notFoundDetail}</p><Link className="primary-button" to="/trips">{t.back}</Link></div>
  return <div className="trip-detail-page"><Link className="back-link" to="/trips"><ArrowLeft size={17}/>{t.back}</Link><div className="trip-management">{editing ? <div className="title-editor"><label className="sr-only" htmlFor="trip-title">{t.rename}</label><input id="trip-title" value={title} maxLength={120} onChange={event => setTitle(event.target.value)}/><button className="small-button" disabled={busy || title.trim().length < 2} onClick={() => void save()}><Save size={14}/>{t.saveName}</button><button className="icon-button" aria-label={t.cancel} onClick={() => { setEditing(false); setTitle(trip.title) }}><X size={17}/></button></div> : <button className="small-button" onClick={() => setEditing(true)}><Edit3 size={14}/>{t.rename}</button>}<button className="danger-button" disabled={busy} onClick={() => void remove()}>{busy ? <RefreshCw className="spin" size={14}/> : <Trash2 size={14}/>} {busy ? t.deleting : t.delete}</button></div>{error && <p className="inline-error" role="alert">{error}</p>}<ItineraryView trip={trip} language={language}/><PlanEditor trip={trip} language={language} onChange={value => { setTrip(value); setTitle(value.title) }}/><RevisionPanel trip={trip} language={language} onChange={value => { setTrip(value); setTitle(value.title) }}/></div>
}
