import { useCallback, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { api, errorMessage } from '../services/apiClient'
import type { User } from '../types/auth'
import { AuthContext as Context } from './authState'
import { useAuthBootstrap } from './useAuthBootstrap'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const pending = useRef<AbortController | null>(null)
  const clear = useCallback(() => { pending.current?.abort(); setUser(null); setLoading(false); setError('') }, [])
  const reload = useCallback(async () => {
    pending.current?.abort()
    const controller = new AbortController(); pending.current = controller
    try {
      const response = await api.get('auth/me/', { signal: controller.signal })
      if (!controller.signal.aborted) { setUser(response.data.data); setError('') }
    }
    catch (failure) {
      if (!controller.signal.aborted && !(failure && typeof failure === 'object' && 'response' in failure &&
        (failure.response as { status?: number })?.status === 401)) setError(errorMessage(failure))
    } finally { if (!controller.signal.aborted) setLoading(false) }
  }, [])
  useAuthBootstrap(setUser, reload, clear)
  async function login(username: string, password: string) {
    pending.current?.abort()
    const response = await api.post('auth/login/', { username, password })
    setUser(response.data.data.user)
  }
  async function logout() { await api.post('auth/logout/'); clear() }
  return <Context.Provider value={{ user, loading, error, reload, login, logout, clear }}>{children}</Context.Provider>
}
