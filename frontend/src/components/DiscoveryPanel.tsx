import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { CheckCircle2, CloudSun, ExternalLink, MapPin, RefreshCw, Search } from 'lucide-react'
import { discoveryCopy } from '../i18n/discovery'
import type { DiscoveryCopy } from '../i18n/discovery'
import { dataError, fetchPlaces, fetchWeather, searchDestinations } from '../services/discovery'
import type { DataError } from '../services/discovery'
import type { Category, DataMode, Destination, DestinationResponse, PlacesResponse, SourceMetadata, WeatherResponse } from '../types/discovery'
import type { Language, TripRequest } from '../types/trip'

interface Remote<T> { loading: boolean; data: T | null; error: DataError | null }
const empty = <T,>(): Remote<T> => ({ loading: false, data: null, error: null })
const categoriesFor: Record<string, Category[]> = { culture: ['historic', 'museum'], art: ['museum'], nature: ['park'], food: ['restaurant'] }

function Source({ metadata, t, language }: { metadata: SourceMetadata; t: DiscoveryCopy; language: Language }) {
  return <div className="source-line">
    {metadata.mode === 'demo' ? <strong>{t.synthetic}</strong> : <>
      <span>{t.source}: </span>{metadata.source_url ? <a href={metadata.source_url} target="_blank" rel="noopener noreferrer">{metadata.source}<ExternalLink size={12}/></a> : <span>{metadata.source}</span>}
      {metadata.cached && <span className="source-cached">{t.cached}</span>}
      {metadata.fetched_at && <span>{t.fetched}: {new Date(metadata.fetched_at).toLocaleString(language === 'tr' ? 'tr-TR' : 'en-GB')}</span>}
    </>}
  </div>
}

function ErrorNotice({ error, retry, t }: { error: DataError; retry: () => void; t: DiscoveryCopy }) {
  const known = error.code in t ? t[error.code as keyof DiscoveryCopy] : t.genericError
  return <div className="data-error" role="alert"><p>{known}</p>{error.retryAfter > 0 && <p>{error.retryAfter} {t.seconds}</p>}<button type="button" onClick={retry}><RefreshCw size={14}/>{t.retry}</button></div>
}

function condition(code: number | null, t: DiscoveryCopy): string {
  if (code === null) return t.conditionUnknown
  if (code === 0) return t.clear
  if ([1, 2, 3].includes(code)) return t.cloudy
  if ([45, 48].includes(code)) return t.fog
  if ([51, 53, 55, 56, 57].includes(code)) return t.drizzle
  if ([61, 63, 65, 66, 67, 80, 81, 82].includes(code)) return t.rainy
  if ([71, 73, 75, 77, 85, 86].includes(code)) return t.snow
  if ([95, 96, 99].includes(code)) return t.storm
  return t.conditionUnknown
}

export function DiscoveryPanel({ request, language, onSelectionChange }: { request: TripRequest; language: Language; onSelectionChange?: (selection: { destination: Destination; mode: DataMode } | null) => void }) {
  const t = discoveryCopy[language]
  const [mode, setMode] = useState<DataMode>('live')
  const [query, setQuery] = useState(request.destination.split(',')[0].trim())
  const [country, setCountry] = useState('')
  const [search, setSearch] = useState<Remote<DestinationResponse>>(empty)
  const [selected, setSelected] = useState<Destination | null>(null)
  const [weather, setWeather] = useState<Remote<WeatherResponse>>(empty)
  const [places, setPlaces] = useState<Remote<PlacesResponse>>(empty)
  const controllers = useRef<Partial<Record<'search' | 'weather' | 'places', AbortController>>>({})
  const epoch = useRef(0)
  const categories = [...new Set(request.interests.flatMap(interest => categoriesFor[interest]))]

  useEffect(() => {
    const active = controllers.current
    return () => { Object.values(active).forEach(controller => controller?.abort()) }
  }, [])

  function controllerFor(key: 'search' | 'weather' | 'places') {
    controllers.current[key]?.abort()
    const controller = new AbortController()
    controllers.current[key] = controller
    return controller
  }

  function resetResults() {
    epoch.current++
    Object.values(controllers.current).forEach(controller => controller?.abort())
    setSelected(null); setSearch(empty()); setWeather(empty()); setPlaces(empty())
    onSelectionChange?.(null)
  }

  async function findCity(event?: FormEvent) {
    event?.preventDefault()
    if (query.trim().length < 2 || (country && !/^[A-Z]{2}$/.test(country))) return
    resetResults()
    const current = epoch.current
    const controller = controllerFor('search')
    setSearch({ loading: true, data: null, error: null })
    try {
      const data = await searchDestinations(query.trim(), country, language, mode, controller.signal)
      if (!controller.signal.aborted && current === epoch.current) setSearch({ loading: false, data, error: null })
    } catch (error) {
      if (!controller.signal.aborted && current === epoch.current) setSearch({ loading: false, data: null, error: dataError(error) })
    }
  }

  async function loadWeather(destination: Destination) {
    const controller = controllerFor('weather')
    setWeather({ loading: true, data: null, error: null })
    try {
      const data = await fetchWeather(destination.id, request.start_date, request.end_date, mode, controller.signal)
      if (!controller.signal.aborted) setWeather({ loading: false, data, error: null })
    } catch (error) {
      if (!controller.signal.aborted) setWeather({ loading: false, data: null, error: dataError(error) })
    }
  }

  async function loadPlaces(destination: Destination) {
    const controller = controllerFor('places')
    setPlaces({ loading: true, data: null, error: null })
    try {
      const data = await fetchPlaces(destination.id, categories, mode, controller.signal)
      if (!controller.signal.aborted) setPlaces({ loading: false, data, error: null })
    } catch (error) {
      if (!controller.signal.aborted) setPlaces({ loading: false, data: null, error: dataError(error) })
    }
  }

  function choose(destination: Destination) {
    setSelected(destination)
    onSelectionChange?.({ destination, mode })
    void loadWeather(destination)
    void loadPlaces(destination)
  }

  const formatDay = (day: string) => new Date(`${day}T12:00:00Z`).toLocaleDateString(language === 'tr' ? 'tr-TR' : 'en-GB', { day: 'numeric', month: 'short', weekday: 'short', timeZone: 'UTC' })

  return <section className="discovery-panel" aria-label={t.title}>
    <span className="tiny-eyebrow">{t.eyebrow}</span><h2>{t.title}</h2><p className="discovery-intro">{t.intro}</p>
    <div className="mode-select"><label htmlFor="data-mode">{t.mode}</label><select id="data-mode" value={mode} onChange={e => { resetResults(); setMode(e.target.value as DataMode) }}><option value="live">{t.live}</option><option value="demo">{t.demo}</option></select></div>
    <p className={`data-mode-notice ${mode === 'demo' ? 'demo-notice' : ''}`} role="status">{mode === 'demo' ? t.demoNotice : t.liveNotice}</p>
    <form className="city-search" onSubmit={findCity}>
      <div className="field"><label htmlFor="city-query">{t.city}</label><input id="city-query" value={query} minLength={2} maxLength={120} required onChange={e => { resetResults(); setQuery(e.target.value) }}/></div>
      <div className="field"><label htmlFor="country-filter">{t.country}</label><input id="country-filter" value={country} maxLength={2} pattern="[A-Z]{2}" placeholder="TR / ES / FR" aria-describedby="country-hint" onChange={e => { resetResults(); setCountry(e.target.value.toUpperCase()) }}/><span id="country-hint" className="field-hint">{t.countryHint}</span></div>
      <button type="submit" className="primary-button" disabled={search.loading || query.trim().length < 2}><Search size={16}/>{t.search}</button>
    </form>
    {search.loading && <p className="data-loading" role="status">{t.searching}</p>}
    {search.error && <ErrorNotice error={search.error} retry={() => void findCity()} t={t}/>}
    {search.data && <div className="city-results">
      {search.data.destinations.length ? <><h3>{t.choose}</h3><div className="city-options">{search.data.destinations.map(destination => <button type="button" key={destination.id} aria-pressed={selected?.id === destination.id} onClick={() => choose(destination)}><MapPin size={18}/><span><strong>{destination.name}</strong><small>{[destination.region, destination.country, destination.country_code].filter(Boolean).join(' · ')}</small></span>{selected?.id === destination.id && <CheckCircle2 size={18}/>}</button>)}</div></> : <p className="empty-data" role="status">{t.noCities}</p>}
      <Source metadata={search.data.metadata} t={t} language={language}/>
    </div>}
    {selected && <>
      <div className="selected-location"><MapPin size={18}/><span>{t.location}: <strong>{selected.name}, {selected.country}</strong><small>{t.timezone}: {selected.timezone} · {selected.latitude.toFixed(4)}, {selected.longitude.toFixed(4)}</small></span></div>
      <section className="data-section" aria-label={t.weather}><h3><CloudSun size={21}/>{t.weather}</h3><p className="section-hint">{t.forecastHint}</p>
        {weather.loading && <p role="status" className="data-loading">{t.loadingWeather}</p>}
        {weather.error && <ErrorNotice error={weather.error} retry={() => void loadWeather(selected)} t={t}/>}
        {weather.data && <><div className="weather-grid">{weather.data.days.map(day => <article className={`weather-day ${!day.available ? 'no-forecast' : ''}`} key={day.date}><h4>{formatDay(day.date)}</h4>{day.available ? <><p className="weather-condition">{condition(day.weather_code, t)}</p><strong className="temperature" aria-label={t.minMax}>{day.temperature_min ?? '—'}° / {day.temperature_max ?? '—'}°</strong><p>{t.rain}: {day.precipitation_mm ?? '—'} mm</p><p>{t.chance}: {day.precipitation_probability ?? '—'}%</p></> : <p>{t[day.reason || 'missing_data']}</p>}</article>)}</div><Source metadata={weather.data.metadata} t={t} language={language}/></>}
      </section>
      <section className="data-section" aria-label={t.places}><h3><MapPin size={20}/>{t.places}</h3><p className="section-hint">{t.placeHint}</p>
        {places.loading && <p role="status" className="data-loading">{t.loadingPlaces}</p>}
        {places.error && <ErrorNotice error={places.error} retry={() => void loadPlaces(selected)} t={t}/>}
        {places.data && <>
          {!places.data.places.length && <p className="empty-data" role="status">{t.noPlaces}</p>}
          <div className="place-results">{places.data.places.map(place => <article className="place-result" key={place.id}><div className="place-result-top"><span className="place-category">{t[place.category]}</span>{place.distance_m !== null && <span>{place.distance_m} m</span>}</div><h4>{place.name}</h4><p>{t[place.indoor]}{place.classification_basis === 'category_inference' ? ` · ${t.inferred}` : place.classification_basis === 'osm_tag' ? ` · ${t.osm_tag}` : ''}</p>{place.coordinate_kind === 'unknown' && <p className="place-caveat">{t.noCoordinates}</p>}{place.coordinate_kind === 'geometry_center' && <p className="place-caveat">{t.geometryCenter}</p>}{place.source_url && <a href={place.source_url} target="_blank" rel="noopener noreferrer">{t.osmLink}<ExternalLink size={13}/></a>}</article>)}</div>
          {places.data.truncated && <p className="section-hint">{t.truncated}</p>}{places.data.skipped_records > 0 && <p className="section-hint">{t.skipped}</p>}
          <Source metadata={places.data.metadata} t={t} language={language}/>
        </>}
      </section>
      <p className="discovery-footnote">{t.notPlan}</p>
    </>}
  </section>
}
