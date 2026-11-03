import { Navigate, Outlet } from 'react-router-dom'
import type { Role } from '../types/auth'
import { useAuth } from './authState'

export function ProtectedRoute({ roles }: { roles?: Role[] }) {
  const { user, loading, error, reload } = useAuth()
  if (loading) return <p role="status">Memeriksa sesi…</p>
  if (error) return <div role="alert"><p>{error}</p><button onClick={() => void reload()}>Coba lagi</button></div>
  if (!user) return <Navigate to="/login" replace />
  if (user.must_change_password) return <Navigate to="/change-password" replace />
  if (roles && !roles.includes(user.role)) return <p role="alert">Anda tidak memiliki akses ke halaman ini.</p>
  return <Outlet />
}
