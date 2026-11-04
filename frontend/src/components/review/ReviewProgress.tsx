import type { AssuranceDetail } from '../../types/assurance'
import { stageLabels, sectionLabels } from '../../utils/reviewLabels'

const actions: Record<string, string> = { SUBMIT: 'Dikirim untuk pemeriksaan', START: 'Mulai pemeriksaan', VERIFY: 'Terverifikasi', NOTE: 'Catatan peninjauan', REQUEST_REVISION: 'Perlu perbaikan', REJECT: 'Perlu perbaikan', REJECT_FINAL: 'Ditolak final', APPROVE: 'Disetujui' }

export function ReviewProgress({ detail }: { detail: AssuranceDetail }) {
  return <section className="panel" aria-label="Tahapan pengajuan"><h2>Tahapan pengajuan</h2>
    <p>Tahap terakhir: <strong>{stageLabels[detail.verification_stage] ?? detail.verification_stage}</strong></p>
    {detail.status === 'REVISION' && <p className="notice">Perlu perbaikan: baca catatan, perbaiki data/berkas, lalu kirim ulang. Kirim ulang memulai pemeriksaan baru.</p>}
    {detail.status === 'REJECTED' && <p className="error">Ditolak final. Pengajuan ini tidak dapat diedit atau dikirim ulang.</p>}
    <ul><li>Data: {detail.data_verified ? 'Terverifikasi' : 'Belum terverifikasi'}</li><li>Berkas: {detail.documents_verified ? 'Terverifikasi' : 'Belum terverifikasi'}</li><li>Persetujuan: {detail.status === 'ACTIVE' ? 'Disetujui dan aktif' : detail.status === 'REJECTED' ? 'Ditolak final' : 'Belum disetujui'}</li></ul>
    <h3>Riwayat pemeriksaan</h3>
    {!detail.review_history?.length && <p>Belum ada riwayat pemeriksaan tercatat.</p>}
    <ol className="review-history">{detail.review_history?.map(event => <li key={event.id}>
      <strong>{actions[event.action] ?? event.action} · {sectionLabels[event.section] ?? event.section}</strong>
      <p>{event.actor_role} · <time dateTime={event.created_at}>{new Date(event.created_at).toLocaleString('id-ID', { timeZone: 'Asia/Jakarta' })} WIB</time></p>
      {event.review_notes && <p className="review-note">{event.review_notes}</p>}
    </li>)}</ol>
  </section>
}
