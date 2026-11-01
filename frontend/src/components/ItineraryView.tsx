import { lazy, Suspense, useMemo, useState } from 'react'
import { CheckCircle2, CloudRain, Database, ExternalLink, MapPin, Navigation } from 'lucide-react'
import { tripsCopy } from '../i18n/trips'
import type { TripRecord } from '../types/itinerary'
import type { Language } from '../types/trip'

const ItineraryMap = lazy(() => import('./ItineraryMap').then(module => ({ default: module.ItineraryMap })))

export function ItineraryView({ trip, language }: { trip: TripRecord; language: Language }) {
  const t = tripsCopy[language]
  const places = useMemo(() => trip.days.flatMap(day => day.activities.map(item => item.place)).filter((place, index, all) => all.findIndex(value => value.id === place.id) === index), [trip.days])
  const [activeId, setActiveId] = useState<string | null>(places[0]?.id ?? null)
  const date = (value: string) => new Date(`${value}T12:00:00Z`).toLocaleDateString(language === 'tr' ? 'tr-TR' : 'en-GB', { weekday: 'long', day: 'numeric', month: 'long', timeZone: 'UTC' })
  const formatNumber = (value: number) => new Intl.NumberFormat(language === 'tr' ? 'tr-TR' : 'en-GB').format(value)
  const activityList = (activities: TripRecord['days'][number]['activities']) => <ol>{activities.map(activity => { const live = activity.place.coordinate_kind !== 'synthetic' && activity.place.latitude != null && activity.place.longitude != null; return <li key={`${activity.period}-${activity.place.id}`}><span>{t[activity.period]}</span><div><button type="button" className="place-focus" aria-pressed={activeId === activity.place.id} onClick={() => setActiveId(activity.place.id)}><strong>{activity.place.name}</strong><MapPin size={14}/></button>{activity.place.description && <p className="activity-description">{activity.place.description}</p>}<p>{activity.reason}</p>{activity.place.pageviews_30d !== null && activity.place.pageviews_30d !== undefined && <small className="activity-interest">{formatNumber(activity.place.pageviews_30d)} · {t.wikiInterest}</small>}<div className="place-links">{activity.place.source_url && <a href={activity.place.source_url} target="_blank" rel="noreferrer">{t.source}<ExternalLink size={13}/></a>}{live ? <a href={`https://www.google.com/maps/dir/?api=1&destination=${activity.place.latitude},${activity.place.longitude}`} target="_blank" rel="noreferrer">{t.route}<Navigation size={13}/></a> : <span>{t.demoLocation}</span>}</div></div></li>})}</ol>
  return <div className="itinerary-result">
    <header><div><span>{trip.generation_mode === 'demo' ? 'Demo' : trip.generation_mode === 'ai' ? 'Gemini' : language === 'tr' ? 'Kurallı plan' : 'Rule-based'}</span><h2>{trip.title}</h2></div><strong><Database size={15}/>{t.saved} · {t.version} {trip.version}</strong></header>
    {trip.warnings.map(warning => <p className="itinerary-warning" key={warning}>{warning}</p>)}
    <section className="map-section"><div className="section-title"><MapPin size={20}/><h3>{t.map}</h3></div><Suspense fallback={<div className="map-fallback" role="status">{language === 'tr' ? 'Harita yükleniyor…' : 'Loading map…'}</div>}><ItineraryMap places={places} activeId={activeId} language={language} onSelect={setActiveId}/></Suspense></section>
    <div className="itinerary-days">{trip.days.map((day, index) => <article key={day.date} className="itinerary-day"><div className="day-heading"><span>{String(index + 1).padStart(2, '0')}</span><div><small>{t.day}</small><h3>{date(day.date)}</h3></div>{day.weather.precipitation_probability != null && <span className="rain-chip"><CloudRain size={14}/>{day.weather.precipitation_probability}%</span>}</div>
      <div className="weather-summary">{day.weather.available ? <><strong>{day.weather.temperature_min}° – {day.weather.temperature_max}°</strong><span>{t.precipitation}: {day.weather.precipitation_probability ?? 0}%</span></> : <span>{t.unavailableWeather}</span>}</div>
      {day.activities.some(activity => activity.place.category !== 'restaurant') && <section className="day-activity-group"><h4>{t.visits}</h4>{activityList(day.activities.filter(activity => activity.place.category !== 'restaurant'))}</section>}
      {day.activities.some(activity => activity.place.category === 'restaurant') && <section className="day-activity-group meal-group"><h4>{t.meals}</h4>{activityList(day.activities.filter(activity => activity.place.category === 'restaurant'))}</section>}
      {day.alternatives.length > 0 && <div className="alternatives"><strong>{t.alternative}</strong>{day.alternatives.map(place => <span key={place.id}>{place.name}</span>)}</div>}
    </article>)}</div>
    <details className="activity-log"><summary>{t.activity}</summary>{trip.agent_activity.map((item, index) => <div key={`${item.name}-${index}`}><CheckCircle2 size={14}/><span><strong>{item.name}</strong>{item.summary}</span></div>)}</details>
    <details className="source-list"><summary>{t.sources}</summary>{trip.sources.map((source, index) => <p key={`${source.source}-${index}`}>{source.source}{source.source_url && <> · <a href={source.source_url} target="_blank" rel="noreferrer">{t.source}<ExternalLink size={12}/></a></>}</p>)}</details>
  </div>
}
