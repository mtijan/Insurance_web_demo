import { Link } from 'react-router-dom'
import type { useWizardSession } from '../../hooks/useWizardSession'
import { ErrorSummary } from '../shared/ErrorSummary'
import { useAuth } from '../../auth/authState'

export function WizardFeedback({ session: { fields, actions, busy } }: { session: ReturnType<typeof useWizardSession> }) {
  return <><ErrorSummary errors={fields.errors} attempt={fields.attempt} />
    {actions.error && <div role="alert" className="error">{actions.error}{actions.detail && <button className="secondary" disabled={busy} onClick={() => void actions.reload()}>Muat ulang status</button>}</div>}
    {actions.notice && <p role="status" className="notice">{actions.notice}</p>}
    {actions.uncertain && <UncertainDraft />}
    {actions.detail && <p className="muted">Draft tersimpan: {new Date(actions.detail.updated_at).toLocaleString('id-ID', { timeZone: 'Asia/Jakarta' })} WIB · <Link to={`/assurances/${actions.detail.id}/edit`}>Buka draft tersimpan</Link></p>}
  </>
}
function UncertainDraft() {
  const { user } = useAuth()
  return <p role="alert" className="error">Hasil simpan belum diketahui. Periksa draft sebelum membuat ulang untuk mencegah duplikasi. <Link to={user?.role === 'DEALER' ? '/assurances/drafts' : '/'}>Periksa draft</Link></p>
}
