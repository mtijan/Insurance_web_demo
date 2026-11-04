import { useEffect } from 'react'
import type { Dispatch, SetStateAction } from 'react'
import type { User } from '../types/auth'

export function useAuthBootstrap(setUser: Dispatch<SetStateAction<User | null>>, reload: () => Promise<void>, clear: () => void) {
  useEffect(() => {
    const restrict = () => { setUser(current => current ? { ...current, must_change_password: true } : null) }
    const revalidate = () => { if (document.visibilityState === 'visible') void reload() }
    window.addEventListener('auth-expired', clear)
    window.addEventListener('password-required', restrict)
    window.addEventListener('permissions-changed', revalidate)
    window.addEventListener('check-session', revalidate)
    window.addEventListener('focus', revalidate)
    document.addEventListener('visibilitychange', revalidate)
    void reload()
    return () => {
      window.removeEventListener('auth-expired', clear)
      window.removeEventListener('password-required', restrict)
      window.removeEventListener('permissions-changed', revalidate)
      window.removeEventListener('check-session', revalidate)
      window.removeEventListener('focus', revalidate)
      document.removeEventListener('visibilitychange', revalidate)
    }
  }, [clear, reload, setUser])
}
