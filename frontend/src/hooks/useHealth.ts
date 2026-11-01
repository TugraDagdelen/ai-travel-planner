import { useEffect, useState } from 'react'
import { fetchHealth } from '../services/api'

export function useHealth() {
  const [status, setStatus] = useState<'loading' | 'online' | 'offline'>('loading')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    fetchHealth(controller.signal).then(() => {
      if (!controller.signal.aborted) setStatus('online')
    }).catch(() => {
      if (!controller.signal.aborted) setStatus('offline')
    })
    return () => controller.abort()
  }, [attempt])

  return { status, retry: () => { setStatus('loading'); setAttempt(value => value + 1) } }
}
