import { useEffect, useState } from 'react'
import L from 'leaflet'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import type { Place } from '../types/discovery'
import type { Language } from '../types/trip'
import { tripsCopy } from '../i18n/trips'

function Focus({ place }: { place: Place | null }) {
  const map = useMap()
  useEffect(() => { if (place?.latitude != null && place.longitude != null) map.flyTo([place.latitude, place.longitude], 14, { duration: .6 }) }, [map, place])
  return null
}

const markerIcon = (active: boolean) => L.divIcon({
  className: 'route-marker-shell',
  html: `<span class="route-marker${active ? ' active' : ''}"></span>`,
  iconSize: [24, 24], iconAnchor: [12, 12], popupAnchor: [0, -11],
})

export function ItineraryMap({ places, activeId, language, onSelect }: { places: Place[]; activeId: string | null; language: Language; onSelect: (id: string) => void }) {
  const t = tripsCopy[language]
  const valid = places.filter(place => place.latitude != null && place.longitude != null)
  const [failed, setFailed] = useState(false)
  if (!valid.length) return <div className="map-fallback" role="status">{t.noCoordinates}</div>
  const active = valid.find(place => place.id === activeId) ?? valid[0]
  return <div className="route-map-wrap" role="region" aria-label={t.map}>
    {failed && <div className="map-error" role="status">{t.mapFailed}</div>}
    <MapContainer className="route-map" center={[active.latitude!, active.longitude!]} zoom={13} scrollWheelZoom={false}>
      <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" eventHandlers={{ tileerror: () => setFailed(true) }}/>
      <Focus place={active}/>
      {valid.map(place => <Marker key={place.id} position={[place.latitude!, place.longitude!]} icon={markerIcon(place.id === active.id)} eventHandlers={{ click: () => onSelect(place.id) }}><Popup>{place.name}</Popup></Marker>)}
    </MapContainer>
  </div>
}
