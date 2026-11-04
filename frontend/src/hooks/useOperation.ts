import { useEffect, useRef, useState } from 'react'
import { errorMessage } from '../services/apiClient'

export function useOperation() {
  const active = useRef<AbortController | null>(null)
  const mounted = useRef(true)
  const [busy, setBusy] = useState(false), [error, setError] = useState('')
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; active.current?.abort() } }, [])
  async function run<T>(task: (signal: AbortSignal) => Promise<T>): Promise<{ ok: true; data: T } | { ok: false; failure?: unknown }> {
    if (active.current) return { ok: false }
    const controller = new AbortController(); active.current = controller
    setBusy(true); setError('')
    try {
      const data = await task(controller.signal)
      return { ok: true, data }
    } catch (failure) {
      if (mounted.current) setError(errorMessage(failure))
      return { ok: false, failure }
    } finally { active.current = null; if (mounted.current) setBusy(false) }
  }
  return { busy, error, run, setError }
}
