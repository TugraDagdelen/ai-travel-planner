import { useEffect, useState } from 'react'
import { Plus, RefreshCw, X } from 'lucide-react'
import { editTripActivity, getTripPlaces, tripError } from '../services/itinerary'
import type { Place } from '../types/discovery'
import type { TripRecord } from '../types/itinerary'
import type { Language } from '../types/trip'
import { tripsCopy } from '../i18n/trips'

export function PlanEditor({ trip, language, onChange }: { trip: TripRecord; language: Language; onChange: (trip: TripRecord) => void }) {
  const t = tripsCopy[language]
  const [places, setPlaces] = useState<Place[]>([])
  const [date, setDate] = useState(trip.days[0]?.date || '')
  const [placeId, setPlaceId] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => { let active = true; void getTripPlaces(trip.id).then(value => { if (active) { setPlaces(value); setPlaceId(value[0]?.id || '') } }).catch(cause => { if (active) setError(tripError(cause).message) }); return () => { active = false } }, [trip.id])
  async function edit(action: 'add' | 'remove', targetDate: string, targetPlace: string) { setBusy(true); setError(''); try { onChange(await editTripActivity(trip.id, action, targetDate, targetPlace)) } catch (cause) { setError(tripError(cause).message) } finally { setBusy(false) } }
  const selectedDay = trip.days.find(day => day.date === date)
  const available = places.filter(place => !selectedDay?.activities.some(activity => activity.place.id === place.id))
  const selectedPlaceId = available.some(place => place.id === placeId) ? placeId : (available[0]?.id || '')
  return <section className="plan-editor" aria-labelledby="plan-editor-title"><div className="section-title"><Plus size={20}/><h2 id="plan-editor-title">{t.editStops}</h2></div><p>{t.editStopsHint}</p>
    <div className="plan-editor-add"><label>{t.chooseDay}<select value={date} onChange={event => setDate(event.target.value)}>{trip.days.map((day, index) => <option value={day.date} key={day.date}>{index + 1}. {t.day} · {day.date}</option>)}</select></label><label>{t.choosePlace}<select value={selectedPlaceId} onChange={event => setPlaceId(event.target.value)}>{available.length ? available.map(place => <option value={place.id} key={place.id}>{place.name} · {t[place.category]} · {place.distance_m ?? '—'} m</option>) : <option value="">{t.noCandidates}</option>}</select></label><button className="small-button" type="button" disabled={busy || !selectedPlaceId || (selectedDay?.activities.length ?? 0) >= 3} onClick={() => void edit('add', date, selectedPlaceId)}>{busy ? <RefreshCw className="spin" size={14}/> : <Plus size={14}/>} {t.addStop}</button></div>
    <div className="plan-editor-days">{trip.days.map((day, index) => <div key={day.date}><strong>{index + 1}. {t.day}</strong>{day.activities.length ? day.activities.map(activity => <span key={`${day.date}-${activity.place.id}`}>{activity.place.name}<button type="button" aria-label={`${t.removeStop}: ${activity.place.name}`} disabled={busy} onClick={() => void edit('remove', day.date, activity.place.id)}><X size={13}/></button></span>) : <em>{t.emptyDay}</em>}</div>)}</div>
    {error && <p className="inline-error" role="alert">{error}</p>}
  </section>
}
