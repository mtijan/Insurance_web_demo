import { useCallback, useState } from 'react'
import type { ReactNode } from 'react'
import { api, errorMessage, setCsrfToken } from '../services/apiClient'
import type { User } from '../types/auth'
import { AuthContext as Context } from './authState'
import { useAuthBootstrap } from './useAuthBootstrap'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const clear = useCallback(() => { setUser(null); setCsrfToken('') }, [])
  const reload = useCallback(async () => {
    try {
      const response = await api.get('auth/me/')
      setUser(response.data.data); setError('')
    }
    catch (failure) {
      if (!(failure && typeof failure === 'object' && 'response' in failure &&
        (failure.response as { status?: number })?.status === 401)) setError(errorMessage(failure))
    } finally { setLoading(false) }
  }, [])
  useAuthBootstrap(setUser, setError, setLoading, clear)
  async function login(username: string, password: string) {
    const response = await api.post('auth/login/', { username, password })
    setCsrfToken(response.data.data.csrf_token)
    setUser(response.data.data.user)
  }
  async function logout() { await api.post('auth/logout/'); clear() }
  return <Context.Provider value={{ user, loading, error, reload, login, logout, clear }}>{children}</Context.Provider>
}
