import { Link } from 'react-router-dom'
import type { useWizardSession } from '../../hooks/useWizardSession'
import { ErrorSummary } from '../shared/ErrorSummary'

export function WizardFeedback({ session: { fields, actions, busy } }: { session: ReturnType<typeof useWizardSession> }) {
  return <><ErrorSummary errors={fields.errors} attempt={fields.attempt} />
    {actions.error && <div role="alert" className="error">{actions.error}<button className="secondary" disabled={busy} onClick={() => void actions.reload()}>Muat ulang status</button></div>}
    {actions.notice && <p role="status" className="notice">{actions.notice}</p>}
    {actions.uncertain && <p role="alert" className="error">Hasil simpan belum diketahui. Periksa daftar jaminan sebelum membuat ulang untuk mencegah duplikasi.</p>}
    {actions.detail && <p className="muted">Draft tersimpan: {new Date(actions.detail.updated_at).toLocaleString('id-ID', { timeZone: 'Asia/Jakarta' })} WIB · <Link to={`/assurances/${actions.detail.id}/edit`}>Buka draft tersimpan</Link></p>}
  </>
}
