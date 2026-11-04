import type { AssuranceDetail } from '../../types/assurance'
import { sectionLabels } from '../../utils/reviewLabels'

const actions: Record<string, string> = { SUBMIT: 'Dikirim untuk pemeriksaan', START: 'Mulai pemeriksaan', VERIFY: 'Terverifikasi', NOTE: 'Catatan peninjauan', REQUEST_REVISION: 'Perlu perbaikan', REJECT: 'Perlu perbaikan', REJECT_FINAL: 'Ditolak final', APPROVE: 'Disetujui' }

export function ReviewHistory({ detail }: { detail: AssuranceDetail }) {
  const history = detail.review_history ?? []
  return <details className="panel history-disclosure"><summary>Riwayat pemeriksaan ({history.length})</summary>
    <h2>Riwayat pemeriksaan</h2>
    {!history.length && <p>Belum ada riwayat pemeriksaan tercatat.</p>}
    <ol className="review-history">{history.map(event => <li key={event.id}>
      <strong>{actions[event.action] ?? event.action} · {sectionLabels[event.section] ?? event.section}</strong>
      <p>{event.actor_role} · <time dateTime={event.created_at}>{new Date(event.created_at).toLocaleString('id-ID', { timeZone: 'Asia/Jakarta' })} WIB</time></p>
      {event.review_notes && <p className="review-note">{event.review_notes}</p>}
    </li>)}</ol>
  </details>
}
