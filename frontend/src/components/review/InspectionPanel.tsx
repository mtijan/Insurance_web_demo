import { useInspection } from '../../hooks/useInspection'
import type { AssuranceDetail } from '../../types/assurance'
import { ConfirmDialog } from '../shared/ConfirmDialog'
import { sectionLabels } from '../../utils/reviewLabels'

export function InspectionPanel({ detail, admin, review }: { detail: AssuranceDetail; admin: boolean; review: ReturnType<typeof useInspection> }) {
  const locked = review.busy || review.mustReload
  return <section className="panel" aria-label="Peninjauan pengajuan"><h2>Peninjauan data dan berkas</h2>
    {review.success && <p role="status">{review.success}</p>}
    {admin && <VerificationActions detail={detail} review={review} />}
    <form onSubmit={event => { event.preventDefault(); void review.submit('NOTE') }}>
      <label>Bagian yang ditinjau<select value={review.section} disabled={locked} onChange={e => review.setSection(e.target.value)}><option value="DATA">Data pengajuan</option><option value="DOCUMENTS">Berkas</option><option value="GENERAL">Umum</option></select></label>
      <label>Catatan kekurangan<textarea autoComplete="off" maxLength={2000} value={review.notes} onChange={e => review.setNotes(e.target.value)} disabled={locked} /></label>
      <p>Jelaskan nama kolom atau jenis berkas dan perbaikan yang diperlukan. Catatan dapat dilihat Dealer. Catatan saja tidak mengubah status.</p>
      {review.error && <p role="alert" className="error">{review.error}</p>}
      <div className="actions"><button type="submit" disabled={locked}>Simpan catatan</button><button type="button" className="secondary" disabled={locked} onClick={() => review.setConfirmRevision(true)}>Kembalikan untuk perbaikan</button></div>
    </form>
    {review.mustReload && <button onClick={() => void review.refresh()}>Muat ulang peninjauan</button>}
    {review.confirmRevision && <RevisionConfirmation review={review} />}
  </section>
}

function VerificationActions({ detail, review }: { detail: AssuranceDetail; review: ReturnType<typeof useInspection> }) {
  const locked = review.busy || review.mustReload
  return <div className="actions">
    <button className="secondary" disabled={locked || detail.data_verified} onClick={() => void review.submit('START', 'DATA')}>Mulai verifikasi data</button>
    <button className="secondary" disabled={locked || detail.data_verified} onClick={() => void review.submit('VERIFY', 'DATA')}>Tandai data terverifikasi</button>
    <button className="secondary" disabled={locked || !detail.data_verified || detail.documents_verified} onClick={() => void review.submit('START', 'DOCUMENTS')}>Mulai verifikasi berkas</button>
    <button className="secondary" disabled={locked || !detail.data_verified || detail.documents_verified} onClick={() => void review.submit('VERIFY', 'DOCUMENTS')}>Tandai berkas terverifikasi</button>
  </div>
}

function RevisionConfirmation({ review }: { review: ReturnType<typeof useInspection> }) {
  return <ConfirmDialog title="Kembalikan pengajuan ke Dealer?" busy={review.busy} close={() => review.setConfirmRevision(false)}>
    <p>Dealer perlu memperbaiki bagian {sectionLabels[review.section]} lalu mengirim ulang. Catatan: {review.notes || 'Belum diisi'}</p>
    {review.error && <p role="alert" className="error">{review.error}</p>}
    <button disabled={review.busy || review.mustReload} onClick={() => void review.submit('REQUEST_REVISION')}>Konfirmasi pengembalian</button>
    {review.mustReload && <button onClick={() => void review.refresh()}>Muat ulang peninjauan</button>}
  </ConfirmDialog>
}
