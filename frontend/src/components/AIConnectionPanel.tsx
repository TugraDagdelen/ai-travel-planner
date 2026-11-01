import { useEffect, useRef, useState } from 'react'
import '../ai.css'
import { CheckCircle2, Sparkles } from 'lucide-react'
import type { Language } from '../types/trip'
import type { AIConnectionResult, AIStatus } from '../types/ai'
import { aiCopy } from '../i18n/ai'
import { fetchAIStatus, checkAIConnection } from '../services/ai'
import { dataError } from '../services/discovery'
import type { DataError } from '../services/discovery'

export function AIConnectionPanel({ language }: { language: Language }) {
  const t = aiCopy[language]
  const [status, setStatus] = useState<AIStatus | null>(null)
  const [result, setResult] = useState<AIConnectionResult | null>(null)
  const [error, setError] = useState<DataError | null>(null)
  const [busy, setBusy] = useState(false)
  const [wait, setWait] = useState(0)
  const active = useRef<AbortController | null>(null)
  const running = useRef(false)
  const until = useRef(0)
  useEffect(() => () => { active.current?.abort() }, [])
  useEffect(() => {
    if (!wait) return
    const timer = window.setInterval(() => setWait(Math.max(0, Math.ceil((until.current - Date.now()) / 1000))), 1000)
    return () => window.clearInterval(timer)
  }, [wait])

  const message = (code: string) => code in t ? t[code as keyof typeof t] : t.generic

  async function run(test: boolean) {
    if (running.current || (test && Date.now() < until.current)) return
    running.current = true
    active.current?.abort()
    const controller = new AbortController()
    active.current = controller
    setBusy(true); setError(null)
    if (test) setResult(null)
    try {
      if (test) {
        const response = await checkAIConnection(language, controller.signal)
        if (!controller.signal.aborted) setResult(response)
      } else {
        const response = await fetchAIStatus(controller.signal)
        if (!controller.signal.aborted) { setStatus(response); setResult(null) }
      }
    } catch (failure) {
      if (!controller.signal.aborted) {
        const parsed = dataError(failure)
        setError(parsed)
        if (parsed.retryAfter > 0) {
          until.current = Date.now() + parsed.retryAfter * 1000
          setWait(parsed.retryAfter)
        }
      }
    } finally {
      running.current = false
      if (!controller.signal.aborted) setBusy(false)
    }
  }

  return <section className="ai-panel" aria-label={t.title} aria-busy={busy}>
    <div className="ai-panel-heading"><Sparkles size={23}/><div><span className="tiny-eyebrow">{t.eyebrow}</span><h2>{t.title}</h2></div></div>
    <p>{t.intro}</p>
    <div className="ai-actions">
      <button className="secondary-button" type="button" disabled={busy} onClick={() => void run(false)}>{status ? t.refresh : t.status}</button>
      {status?.gemini.enabled && <button className="primary-button" type="button" disabled={busy || wait > 0} onClick={() => void run(true)}>{t.test}</button>}
    </div>
    {busy && <p role="status">{t.busy}</p>}
    {status && <div className="ai-status" role="status"><strong>{message(status.gemini.reason)}</strong><p>{status.gemini.enabled ? t.privacy : t.setup}</p><p className="section-hint">{t.accountNote}</p></div>}
    {error && <div className="data-error" role="alert"><p>{message(error.code)}</p></div>}
    {wait > 0 && <p className="section-hint">{t.wait} {wait}</p>}
    {result && <div className="ai-success" role="status"><strong><CheckCircle2 size={17}/>{t.verified}</strong><p>{result.message}</p><small>{result.model} · {t.checked}: {new Date(result.checked_at).toLocaleString(language === 'tr' ? 'tr-TR' : 'en-GB')}</small></div>}
    <p className="ai-grounding-note">{t.grounding}</p>
  </section>
}
