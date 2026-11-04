import { ConfirmDialog } from '../shared/ConfirmDialog'
import type { useReviewDecision } from '../../hooks/useReviewDecision'

export function ReviewActions({ review }: { review: ReturnType<typeof useReviewDecision> }) {
  return <section className="panel"><h2>Keputusan verifikasi</h2>
    <p>Setujui mengonfirmasi pemeriksaan data dan berkas, menerbitkan nomor, lalu mengunci jaminan. Minta perbaikan memungkinkan pengiriman ulang. Tolak final mengakhiri pengajuan.</p>
    <div className="actions"><button disabled={review.busy || review.mustReload} onClick={() => review.setDecision('APPROVE')}>Setujui & terbitkan</button><button className="secondary" disabled={review.busy || review.mustReload} onClick={() => review.setDecision('REQUEST_REVISION')}>Minta perbaikan</button><button className="secondary" disabled={review.busy || review.mustReload} onClick={() => review.setDecision('REJECT_FINAL')}>Tolak final</button></div>
    {review.mustReload && <p className="error">Status mungkin berubah atau permintaan gagal. Muat ulang sebelum melanjutkan. <button onClick={() => void review.refresh()}>Muat ulang status</button></p>}
    {review.decision && <ConfirmDialog title={review.decision === 'APPROVE' ? 'Setujui & terbitkan jaminan?' : review.decision === 'REJECT_FINAL' ? 'Tolak pengajuan secara final?' : 'Minta perbaikan pengajuan?'} busy={review.busy} close={() => review.setDecision(null)}>
      <ReviewDecisionForm review={review} />
    </ConfirmDialog>}
  </section>
}

function ReviewDecisionForm({ review }: { review: ReturnType<typeof useReviewDecision> }) {
  return <form noValidate onSubmit={event => { event.preventDefault(); void review.submit() }}>
        <p>{review.decision === 'APPROVE' ? 'Saya telah memeriksa data dan berkas. Sesudah berhasil, pengajuan tidak dapat diedit, termasuk oleh Super Admin.' : review.decision === 'REJECT_FINAL' ? 'Pengajuan dikunci dan tidak dapat diperbaiki atau dikirim ulang. Isi alasan penolakan final.' : 'Pengaju dapat memperbaiki dokumen/data lalu mengirim ulang. Ini bukan penolakan permanen.'}</p>
        <label>Catatan pemeriksaan{review.decision !== 'APPROVE' ? ' (wajib)' : ' (opsional)'}<textarea autoComplete="off" maxLength={2000} value={review.notes} onChange={e => review.setNotes(e.target.value)} required={review.decision !== 'APPROVE'} disabled={review.busy || review.mustReload} /></label>
        {review.error && <p role="alert" className="error">{review.error}</p>}
        {review.mustReload && <button type="button" onClick={() => void review.refresh()}>Muat ulang status</button>}
        <button disabled={review.busy || review.mustReload} type="submit">{review.busy ? 'Memproses…' : 'Konfirmasi keputusan'}</button>
      </form>
}
