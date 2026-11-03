import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../auth/authState'
import { errorMessage } from '../../services/apiClient'

export function Navbar() {
  const { user, logout } = useAuth()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  return <>
    <nav aria-label="Navigasi utama" className="toolbar">
      <Link to="/">Jaminan</Link>
      {user?.role === 'SUPER_ADMIN' && <Link to="/audit">Riwayat audit</Link>}
      <span>{user?.username} · {user?.role.replaceAll('_', ' ')}</span>
      <button disabled={busy} className="secondary" onClick={async () => {
        setBusy(true); setError('')
        try { await logout() } catch (failure) { setError(errorMessage(failure)) }
        finally { setBusy(false) }
      }}>{busy ? 'Memproses…' : 'Keluar'}</button>
    </nav>
    {error && <p role="alert" className="error">{error}</p>}
  </>
}
