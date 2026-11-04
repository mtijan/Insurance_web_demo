import { ConfirmDialog } from '../shared/ConfirmDialog'
import type { useReviewDecision } from '../../hooks/useReviewDecision'

export function ReviewActions({ review }: { review: ReturnType<typeof useReviewDecision> }) {
  return <section className="panel"><h2>Keputusan verifikasi</h2>
    <p>Ambil keputusan setelah memeriksa data dan berkas. Untuk meminta revisi, isi bagian dan catatan pada peninjauan.</p>
    <div className="actions"><button disabled={review.busy || review.mustReload} onClick={() => review.setDecision('APPROVE')}>Setujui & terbitkan</button><a href="#inspection">Catat kekurangan atau minta revisi</a><button className="secondary danger-action" disabled={review.busy || review.mustReload} onClick={() => review.setDecision('REJECT_FINAL')}>Tolak final</button></div>
    {review.mustReload && <p className="error">Status mungkin berubah atau permintaan gagal. Muat ulang sebelum melanjutkan. <button onClick={() => void review.refresh()}>Muat ulang status</button></p>}
    {review.decision && <ConfirmDialog title={review.decision === 'APPROVE' ? 'Setujui & terbitkan jaminan?' : 'Tolak pengajuan secara final?'} busy={review.busy} close={() => review.setDecision(null)}>
      <ReviewDecisionForm review={review} />
    </ConfirmDialog>}
  </section>
}

function ReviewDecisionForm({ review }: { review: ReturnType<typeof useReviewDecision> }) {
  return <form noValidate onSubmit={event => { event.preventDefault(); void review.submit() }}>
        <p>{review.decision === 'APPROVE' ? 'Saya telah memeriksa data dan berkas. Sesudah berhasil, pengajuan tidak dapat diedit, termasuk oleh Super Admin.' : 'Pengajuan dikunci dan tidak dapat diperbaiki atau dikirim ulang. Isi alasan penolakan final.'}</p>
        <label>Catatan pemeriksaan{review.decision !== 'APPROVE' ? ' (wajib)' : ' (opsional)'}<textarea autoComplete="off" maxLength={2000} value={review.notes} onChange={e => review.setNotes(e.target.value)} required={review.decision !== 'APPROVE'} disabled={review.busy || review.mustReload} /></label>
        {review.error && <p role="alert" className="error">{review.error}</p>}
        {review.mustReload && <button type="button" onClick={() => void review.refresh()}>Muat ulang status</button>}
        <button disabled={review.busy || review.mustReload} type="submit">{review.busy ? 'Memproses…' : 'Konfirmasi keputusan'}</button>
      </form>
}
