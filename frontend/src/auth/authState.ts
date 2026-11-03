import { createContext, useContext } from 'react'
import type { User } from '../types/auth'

interface AuthState {
  user: User | null
  loading: boolean
  error: string
  reload: () => Promise<void>
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  clear: () => void
}
export const AuthContext = createContext<AuthState | null>(null)
export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('AuthProvider is required')
  return value
}
