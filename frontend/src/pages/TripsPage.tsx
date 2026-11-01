import { useEffect, useState } from 'react'
import { ArrowRight, CalendarDays, MapPin, RefreshCw } from 'lucide-react'
import { Link } from 'react-router-dom'
import { listTrips, tripError } from '../services/itinerary'
import { tripsCopy } from '../i18n/trips'
import type { TripSummary } from '../types/itinerary'
import type { Language } from '../types/trip'

export function TripsPage({ language }: { language: Language }) {
  const t = tripsCopy[language]
  const [trips, setTrips] = useState<TripSummary[]>([]), [loading, setLoading] = useState(true), [error, setError] = useState('')
  async function load() { setLoading(true); setError(''); try { setTrips((await listTrips()).trips) } catch (cause) { setError(tripError(cause).message) } finally { setLoading(false) } }
  useEffect(() => { let active = true; listTrips().then(value => { if (active) setTrips(value.trips) }).catch(cause => { if (active) setError(tripError(cause).message) }).finally(() => { if (active) setLoading(false) }); return () => { active = false } }, [])
  const date = (value: string) => new Date(`${value}T12:00:00Z`).toLocaleDateString(language === 'tr' ? 'tr-TR' : 'en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })
  const days = (start: string, end: string) => Math.round((Date.parse(end) - Date.parse(start)) / 86400000) + 1
  return <div className="trips-page"><div className="eyebrow"><span/>{t.eyebrow}</div><h1>{t.title}</h1><p className="trips-intro">{t.intro}</p>
    {loading ? <div className="page-state" role="status"><RefreshCw className="spin"/>{t.loading}</div> : error ? <div className="data-error" role="alert"><p>{t.loadFailed}</p><p>{error}</p><button onClick={() => void load()}><RefreshCw size={14}/>{t.retry}</button></div> : trips.length === 0 ? <div className="empty-trip-list"><MapPin size={32}/><h2>{t.empty}</h2><p>{t.emptyDetail}</p><Link className="primary-button" to="/">{t.create}</Link></div> : <div className="trip-grid">{trips.map(trip => <article className="trip-card" key={trip.id}><span>{trip.generation_mode === 'demo' ? 'Demo' : trip.generation_mode === 'ai' ? 'Gemini' : language === 'tr' ? 'Kurallı' : 'Rule-based'}</span><h2>{trip.title}</h2><p><MapPin size={14}/>{trip.destination_name}</p><p><CalendarDays size={14}/>{date(trip.start_date)} — {date(trip.end_date)} · {days(trip.start_date, trip.end_date)} {t.days}</p><footer><small>{t.version} {trip.version} · {t.updated} {new Date(trip.updated_at).toLocaleDateString(language === 'tr' ? 'tr-TR' : 'en-GB')}</small><Link to={`/trips/${trip.id}`}>{t.open}<ArrowRight size={14}/></Link></footer></article>)}</div>}
  </div>
}
