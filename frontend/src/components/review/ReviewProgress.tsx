import type { AssuranceDetail } from '../../types/assurance'
import { workflowStage, verificationLabel } from '../../utils/workflowPresentation'

export function ReviewProgress({ detail }: { detail: AssuranceDetail }) {
  return <section className="panel" aria-label="Tahapan pengajuan"><h2>Tahapan pengajuan</h2>
    <p>Tahap saat ini: <strong>{workflowStage(detail.status, detail.verification_stage)}</strong></p>
    <ul><li>Data: {verificationLabel(detail.status, detail.data_verified)}</li><li>Berkas: {verificationLabel(detail.status, detail.documents_verified)}</li><li>Persetujuan: {detail.status === 'ACTIVE' ? 'Disetujui dan aktif' : detail.status === 'REJECTED' ? 'Ditolak final' : 'Belum disetujui'}</li></ul>
    {detail.status === 'REVISION' && <p className="muted">Hasil verifikasi sebelum permintaan perbaikan tersimpan di riwayat. Data dan berkas akan diperiksa ulang setelah dikirim.</p>}
  </section>
}
