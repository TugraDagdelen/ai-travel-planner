import { ArrowUpRight } from 'lucide-react'
import { TravelForm } from '../components/TravelForm'
import { TravelIllustration } from '../components/TravelIllustration'
import { HealthStatus } from '../components/HealthStatus'
import { AIConnectionPanel } from '../components/AIConnectionPanel'
import type { Copy } from '../i18n/copy'
import type { TripRequest, ValidatedTripRequest } from '../types/trip'

export function HomePage({ t, draft, onChange, onValidated }: { t: Copy; draft: TripRequest; onChange: (draft: TripRequest) => void; onValidated: (result: ValidatedTripRequest) => void }) {
  return <>
    <section className="hero"><div className="eyebrow"><span/>{t.eyebrow}</div><h1>{t.title}<br/><em>{t.titleAccent}</em></h1><p>{t.intro}</p><span className="hero-compass" aria-hidden="true"><ArrowUpRight strokeWidth={1} size={52}/></span></section>
    <div className="planning-grid">
      <TravelForm t={t} draft={draft} onChange={onChange} onValidated={onValidated}/>
      <aside className="inspiration"><TravelIllustration t={t}/><HealthStatus t={t}/></aside>
    </div>
    <section className="journey-steps"><h2>{t.futureTitle}</h2><div className="steps-grid">{t.steps.map(([number, title, description]) => <article className="step" key={number}><div className="step-top"><span className="step-number">{number}</span><span className="step-state current">{t.now}</span></div><h3>{title}</h3><p>{description}</p></article>)}</div></section>
    <AIConnectionPanel language={draft.language}/>
  </>
}
