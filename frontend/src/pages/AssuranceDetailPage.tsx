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
import { ApplicationOverview } from '../components/assurances/ApplicationOverview'
import { ReviewHistory } from '../components/review/ReviewHistory'
import { DocumentPreviewProvider } from '../components/documents/DocumentPreviewProvider'

export function AssuranceDetailPage() {
  const { id } = useParams()
  return <DocumentPreviewProvider key={id}><DetailWorkspace id={id!} /></DocumentPreviewProvider>
}
function DetailWorkspace({ id }: { id: string }) {
  const { user } = useAuth()
  const resource = useResource<AssuranceDetail>(`assurances/${id}/`)
  const inspection = useInspection(id, resource.reload)
  const current = resource.data
  return <section aria-busy={resource.loading}>
    <Link to="/">Kembali ke daftar jaminan</Link><h1>Detail pengajuan</h1>
    <Feedback {...resource} retry={resource.reload} />
    {current && <>
      <ApplicationOverview detail={current}><DetailActions detail={current} role={user?.role} /></ApplicationOverview>
      <ReviewProgress detail={current} />
      {current.status === 'SUBMITTED' && user?.role === 'AGENT' && <InspectionPanel detail={current} admin={false} review={inspection} />}
      {current.status !== 'SUBMITTED' && inspection.success && <p role="status">{inspection.success}</p>}
      <details className="panel data-disclosure"><summary>Data pengajuan dan premi</summary><AssuranceSummary detail={current} /></details>
      <h2>Berkas pengajuan</h2><p>JPEG, PNG, atau WebP maksimal 5 MiB per berkas.</p>
      {!current.can_edit && <p>Dokumen hanya dapat dibaca pada akun atau status ini.</p>}
      <DocumentSlots detail={current} reload={resource.reload} />
      <ReviewHistory detail={current} />
    </>}
  </section>
}
function DetailActions({ detail, role }: { detail: AssuranceDetail; role?: string }) {
  return <>
    {detail.can_edit && <Link className="download" to={`/assurances/${detail.id}/edit`}>{detail.status === 'REVISION' ? 'Perbaiki pengajuan' : 'Lanjutkan pengajuan'}</Link>}
    {detail.status === 'ACTIVE' && <PdfDownload id={detail.id} />}
    {detail.status === 'SUBMITTED' && role === 'AGENT' && <a className="download" href="#inspection">Tinjau pengajuan</a>}
    {detail.status === 'SUBMITTED' && (role === 'ADMIN' || role === 'SUPER_ADMIN') && <Link className="download" to={`/review/${detail.id}`}>Verifikasi pengajuan</Link>}
  </>
}
