import { useEffect, useState } from 'react'
import { Compass, Globe2, MoveUpRight } from 'lucide-react'
import { Link, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { copy } from './i18n/copy'
import { HomePage } from './pages/HomePage'
import { PlannerPage } from './pages/PlannerPage'
import { EmptyState } from './components/EmptyState'
import { TripsPage } from './pages/TripsPage'
import { TripDetailPage } from './pages/TripDetailPage'
import type { Language, TripRequest, ValidatedTripRequest } from './types/trip'

const initialDraft: TripRequest = { destination: '', start_date: '', end_date: '', interests: [], budget: 'balanced', pace: 'balanced', language: 'tr', notes: '' }

export default function App() {
  const [language, setLanguage] = useState<Language>('tr')
  const [draft, setDraft] = useState<TripRequest>(initialDraft)
  const [validated, setValidated] = useState<ValidatedTripRequest | null>(null)
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const t = copy[language]

  useEffect(() => { document.documentElement.lang = language }, [language])
  useEffect(() => { document.getElementById('main-content')?.focus({ preventScroll: true }); window.scrollTo({ top: 0, behavior: 'instant' }) }, [pathname])

  function changeLanguage(next: Language) {
    setLanguage(next)
    setDraft(value => ({ ...value, language: next }))
  }

  function onValidated(result: ValidatedTripRequest) {
    setValidated(result)
    setDraft(result.request)
    navigate('/planner')
  }

  return <div className="app-shell">
    <a className="skip-link" href="#main-content">{language === 'tr' ? 'İçeriğe geç' : 'Skip to content'}</a>
    <header className="site-header"><Link className="brand" to="/" aria-label="Rota — AI Travel Planner"><span className="brand-icon"><Compass size={24} strokeWidth={1.6}/></span><span>rota<span className="brand-dot">.</span><small>AI TRAVEL PLANNER</small></span></Link>
      <nav aria-label={language === 'tr' ? 'Ana menü' : 'Main navigation'}><NavLink to="/" end>{t.home}</NavLink><NavLink to="/trips">{t.trips}</NavLink></nav>
      <div className="language-switch"><Globe2 size={17} aria-hidden="true"/><label className="sr-only" htmlFor="language">{t.language}</label><select id="language" value={language} onChange={e => changeLanguage(e.target.value as Language)}><option value="tr">TR</option><option value="en">EN</option></select></div>
    </header>
    <main id="main-content" tabIndex={-1}><Routes>
      <Route path="/" element={<HomePage t={t} draft={draft} onChange={setDraft} onValidated={onValidated}/>}/>
      <Route path="/planner" element={<PlannerPage t={t} trip={validated} language={language}/>}/>
      <Route path="/trips" element={<TripsPage language={language}/>}/>
      <Route path="/trips/:id" element={<TripDetailPage language={language}/>}/>
      <Route path="*" element={<EmptyState title={t.noPage} description={t.noPageDetail} action={t.startJourney}/>}/>
    </Routes></main>
    <footer className="site-footer"><span className="footer-motto"><MoveUpRight size={17}/>{t.footer}</span><span>{t.stage}</span><span>Rota © {new Date().getFullYear()}</span></footer>
  </div>
}
