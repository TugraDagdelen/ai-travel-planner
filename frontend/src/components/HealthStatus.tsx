import { CircleCheck, RefreshCw, WifiOff } from 'lucide-react'
import { useHealth } from '../hooks/useHealth'
import type { Copy } from '../i18n/copy'

export function HealthStatus({ t }: { t: Copy }) {
  const { status, retry } = useHealth()
  const Icon = status === 'online' ? CircleCheck : status === 'offline' ? WifiOff : RefreshCw
  return <div className={`connection connection-${status}`}>
    <Icon size={16} aria-hidden="true" className={status === 'loading' ? 'spin' : ''} />
    <div role="status" aria-live="polite">
      <strong>{status === 'loading' ? t.connecting : t[status]}</strong>
      <span>{status === 'online' ? t.successDetail : status === 'offline' ? t.errorDetail : t.connectionDescription}</span>
    </div>
    <button type="button" className="icon-button" disabled={status === 'loading'} onClick={retry} aria-label={t.retry} title={t.retry}><RefreshCw size={16} /></button>
  </div>
}
