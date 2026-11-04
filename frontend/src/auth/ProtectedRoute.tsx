import { Link, Navigate, Outlet } from 'react-router-dom'
import type { Role } from '../types/auth'
import { useAuth } from './authState'

export function ProtectedRoute({ roles }: { roles?: Role[] }) {
  const { user, loading, error, reload } = useAuth()
  if (loading) return <main id="main" tabIndex={-1}><h1>Memeriksa sesi</h1><p role="status">Memeriksa sesi…</p></main>
  if (error) return <main id="main" tabIndex={-1}><h1>Sesi belum dapat diperiksa</h1><div role="alert"><p>{error}</p><button onClick={() => void reload()}>Coba lagi</button></div></main>
  if (!user) return <Navigate to="/login" replace />
  if (user.must_change_password) return <Navigate to="/change-password" replace />
  if (roles && !roles.includes(user.role)) return <section><h1>Akses ditolak</h1><p role="alert">Anda tidak memiliki akses ke halaman ini.</p><Link to="/">Kembali ke daftar jaminan</Link></section>
  return <Outlet />
}
