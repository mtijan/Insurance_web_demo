import { useState } from 'react'
import { LogOut } from 'lucide-react'
import { useAuth } from '../../auth/authState'
import { errorMessage } from '../../services/apiClient'
import { useNavigationSafety } from './navigationSafety'
import { ConfirmDialog } from '../shared/ConfirmDialog'

export function LogoutButton({ compact }: { compact?: boolean }) {
  const { logout } = useAuth()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [confirm, setConfirm] = useState(false)
  const { safety } = useNavigationSafety()
  async function leave() {
    if (busy) return
    setBusy(true); setError('')
    try { await logout() } catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <><button className="logout" aria-label="Keluar" disabled={busy || safety.busy} onClick={() => { if (safety.dirty) setConfirm(true); else void leave() }}><LogOut size={20} aria-hidden="true" />{!compact && (busy ? 'Memproses…' : 'Keluar')}</button>{error && <p role="alert">{error}</p>}
    {confirm && <ConfirmDialog title="Keluar dengan perubahan belum disimpan?" busy={busy} close={() => setConfirm(false)}><p>Isian yang belum disimpan akan hilang. Draft yang sudah tersimpan tetap berada di server.</p>{error && <p role="alert" className="error">{error}</p>}<button disabled={busy} onClick={() => void leave()}>Konfirmasi keluar</button></ConfirmDialog>}
  </>
}
