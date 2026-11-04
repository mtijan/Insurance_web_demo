import { Link, useParams } from 'react-router-dom'
import { useResource } from '../hooks/useResource'
import type { AssuranceDetail } from '../types/assurance'
import { Feedback } from '../components/shared/Feedback'
import { AssuranceSummary } from '../components/assurances/AssuranceSummary'
import { PdfDownload } from '../components/assurances/PdfDownload'
import { DocumentSlots } from '../components/documents/DocumentSlots'
import { useAuth } from '../auth/authState'
import { InspectionPanel } from '../components/review/InspectionPanel'
import { ReviewProgress } from '../components/review/ReviewProgress'
import { useInspection } from '../hooks/useInspection'

export function AssuranceDetailPage() {
  const { id } = useParams()
  return <DetailWorkspace key={id} id={id!} />
}
function DetailWorkspace({ id }: { id: string }) {
  const { user } = useAuth()
  const resource = useResource<AssuranceDetail>(`assurances/${id}/`)
  const inspection = useInspection(id, resource.reload)
  const current = resource.data
  return <section aria-busy={resource.loading}>
    <Link to="/">Kembali ke daftar jaminan</Link><h1>Dokumen jaminan</h1>
    <Feedback {...resource} retry={resource.reload} />
    {current && <>
      <AssuranceSummary detail={current} />
      <ReviewProgress detail={current} />
      {current.status === 'SUBMITTED' && user?.role === 'AGENT' && <InspectionPanel detail={current} admin={false} review={inspection} />}
      {current.status !== 'SUBMITTED' && inspection.success && <p role="status">{inspection.success}</p>}
      {current.can_edit && <Link className="download" to={`/assurances/${current.id}/edit`}>Lanjutkan pengajuan</Link>}
      {current.status === 'ACTIVE' && <PdfDownload id={current.id} />}
      <p>JPEG, PNG, atau WebP maksimal 5 MiB per berkas. Untuk mengganti berkas, unggah pengganti dahulu, lalu hapus berkas lama.</p>
      {!current.can_edit && <p>Dokumen hanya dapat dibaca pada akun atau status ini.</p>}
      <DocumentSlots detail={current} reload={resource.reload} />
    </>}
  </section>
}
