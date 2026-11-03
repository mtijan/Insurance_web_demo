import { useEffect } from 'react'
import type { Dispatch, SetStateAction } from 'react'
import type { User } from '../types/auth'
import { api, errorMessage } from '../services/apiClient'

export function useAuthBootstrap(setUser: Dispatch<SetStateAction<User | null>>,
  setError: Dispatch<SetStateAction<string>>, setLoading: Dispatch<SetStateAction<boolean>>, clear: () => void) {
  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const response = await api.get('auth/me/')
        if (!cancelled) { setUser(response.data.data); setError('') }
      } catch (failure) {
        if (!cancelled && !(failure && typeof failure === 'object' && 'response' in failure &&
          (failure.response as { status?: number })?.status === 401)) setError(errorMessage(failure))
      } finally { if (!cancelled) setLoading(false) }
    }
    void load()
    const restrict = () => { setUser(current => current ? { ...current, must_change_password: true } : null) }
    window.addEventListener('auth-expired', clear)
    window.addEventListener('password-required', restrict)
    return () => {
      cancelled = true
      window.removeEventListener('auth-expired', clear)
      window.removeEventListener('password-required', restrict)
    }
  }, [clear, setError, setLoading, setUser])
}
