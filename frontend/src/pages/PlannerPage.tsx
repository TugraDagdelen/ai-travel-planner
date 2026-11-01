import { useState } from 'react'
import { ArrowLeft, CalendarDays, CheckCircle2, MapPin } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Copy } from '../i18n/copy'
import type { Language, ValidatedTripRequest } from '../types/trip'
import { EmptyState } from '../components/EmptyState'
import { DiscoveryPanel } from '../components/DiscoveryPanel'
import { AIConnectionPanel } from '../components/AIConnectionPanel'
import { ItineraryPanel } from '../components/ItineraryPanel'
import type { DestinationSelection } from '../components/ItineraryPanel'

export function PlannerPage({ t, trip, language }: { t: Copy; trip: ValidatedTripRequest | null; language: Language }) {
  const [selection, setSelection] = useState<DestinationSelection | null>(null)
  if (!trip) return <EmptyState title={t.noDraft} description={t.noDraftDetail} action={t.startJourney}/>
  const formatDate = (date: string) => new Intl.DateTimeFormat(language === 'tr' ? 'tr-TR' : 'en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${date}T12:00:00Z`))
  return <div className="review-page">
    <Link to="/" className="back-link"><ArrowLeft size={17}/>{t.back}</Link>
    <div className="eyebrow"><span/>{t.reviewEyebrow}</div><h1>{t.reviewTitle}</h1><p className="review-intro">{t.reviewIntro}</p>
    <section className="review-card"><div className="review-card-heading"><MapPin size={27}/><h2>{trip.request.destination}</h2><span className="pill">{trip.duration_days} {t.days}</span></div><div className="validation-badge"><CheckCircle2 size={16}/>{t.validated}</div>
      <dl className="summary-grid"><div className="summary-wide"><dt><CalendarDays size={15}/>{t.dateLabel}</dt><dd>{formatDate(trip.request.start_date)} — {formatDate(trip.request.end_date)}</dd></div><div><dt>{t.budget}</dt><dd>{t[trip.request.budget]}</dd></div><div><dt>{t.pace}</dt><dd>{t[trip.request.pace]}</dd></div><div className="summary-wide"><dt>{t.interests}</dt><dd className="summary-interests">{trip.request.interests.map(interest => <span key={interest}>{t[interest]}</span>)}</dd></div>{trip.request.notes && <div className="summary-wide"><dt>{t.notes}</dt><dd className="notes-content">{trip.request.notes}</dd></div>}</dl>
    </section>
    <DiscoveryPanel request={trip.request} language={language} onSelectionChange={setSelection}/>
    <ItineraryPanel key={`${selection?.mode || 'none'}:${selection?.destination.id || 'none'}`} request={trip.request} language={language} selection={selection}/>
    <AIConnectionPanel language={language}/>
  </div>
}
