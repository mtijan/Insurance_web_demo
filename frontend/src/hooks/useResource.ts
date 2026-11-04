import { useCallback, useEffect, useRef, useState } from 'react'
import { api, errorMessage } from '../services/apiClient'
import { useAuth } from '../auth/authState'
import type { Envelope } from '../types/auth'

export function useResource<T>(path: string, raw = false) {
  const { user } = useAuth()
  const scope = `${user?.id}:${user?.role}:${path}`
  const [state, setState] = useState<{ key: string; data?: T; error: string; loading: boolean }>({ key: '', error: '', loading: true })
  const active = useRef<AbortController | null>(null)
  const load = useCallback(async (controller: AbortController) => {
    if (!path) return undefined
    try {
      const response = await api.get<T | Envelope<T>>(path, { signal: controller.signal })
      const data = raw ? response.data as T : (response.data as Envelope<T>).data
      if (!controller.signal.aborted) setState({ key: scope, data, error: '', loading: false })
      return controller.signal.aborted ? undefined : data
    } catch (failure) {
      if (!controller.signal.aborted) setState({ key: scope, error: errorMessage(failure), loading: false })
      return undefined
    }
  }, [path, raw, scope])
  const reload = useCallback(async () => {
    active.current?.abort(); const controller = new AbortController(); active.current = controller
    setState({ key: scope, error: '', loading: true })
    return load(controller)
  }, [load, scope])
  useEffect(() => {
    const controller = new AbortController(); active.current = controller
    queueMicrotask(() => { if (!controller.signal.aborted) void load(controller) })
    return () => controller.abort()
  }, [load])
  const current = !path ? { data: undefined, error: '', loading: false } : state.key === scope ? state : { data: undefined, error: '', loading: true }
  return { ...current, reload }
}
