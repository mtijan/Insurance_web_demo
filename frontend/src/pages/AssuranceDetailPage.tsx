import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, FilePenLine, ScanSearch, ShieldCheck } from 'lucide-react'
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
import { AssuranceNotesPanel } from '../components/review/AssuranceNotesPanel'
import { DocumentPreviewProvider } from '../components/documents/DocumentPreviewProvider'
import { DraftDeleteAction } from '../components/assurances/DraftDeleteAction'
import { assuranceReturnLabel, assuranceReturnPath, isUuidParam, safeBackTarget } from '../utils/roleLabels'

export function AssuranceDetailPage() {
  const { id } = useParams()
  if (!isUuidParam(id)) return <section className="panel" role="alert"><h1>Detail pengajuan</h1><p>ID pengajuan tidak valid.</p></section>
  return <DocumentPreviewProvider key={id}><DetailWorkspace id={id} /></DocumentPreviewProvider>
}
function DetailWorkspace({ id }: { id: string }) {
  const { user } = useAuth()
  const { state } = useLocation()
  const navigate = useNavigate()
  const resource = useResource<AssuranceDetail>(`assurances/${id}/`)
  const inspection = useInspection(id, resource.reload)
  const current = resource.data
  const backTo = safeBackTarget(state, assuranceReturnPath(user?.role, current?.dealer.id, current?.status))
  return <section aria-busy={resource.loading}>
    <Link className="back-link" to={backTo}><ArrowLeft size={16} aria-hidden="true" />{assuranceReturnLabel(user?.role)}</Link><h1>Detail pengajuan</h1>
    <Feedback {...resource} retry={resource.reload} />
    {current && <>
      <ApplicationOverview detail={current}><DetailActions detail={current} role={user?.role} backTo={backTo} onDeleted={() => navigate(backTo, { replace: true })} /></ApplicationOverview>
      <ReviewProgress detail={current} />
      {current.status === 'SUBMITTED' && user?.role === 'AGENT' && <InspectionPanel detail={current} admin={false} review={inspection} />}
      {current.status !== 'SUBMITTED' && inspection.success && <p role="status">{inspection.success}</p>}
      <details className="panel data-disclosure"><summary>Data pengajuan dan premi</summary><AssuranceSummary detail={current} /></details>
      <h2>Berkas pengajuan</h2><p>JPEG, PNG, atau WebP maksimal 5 MiB per berkas.</p>
      {!current.can_edit && <p>Dokumen hanya dapat dibaca pada akun atau status ini.</p>}
      <DocumentSlots detail={current} reload={resource.reload} />
      <AssuranceNotesPanel detail={current} />
      <ReviewHistory detail={current} />
    </>}
  </section>
}
function DetailActions({ detail, role, backTo, onDeleted }: { detail: AssuranceDetail; role?: string; backTo: string; onDeleted: () => void }) {
  return <>
    {detail.can_edit && <Link className="download" to={`/assurances/${detail.id}/edit`} state={{ backTo }}><FilePenLine size={18} aria-hidden="true" />{detail.status === 'REVISION' ? 'Perbaiki pengajuan' : 'Lanjutkan pengajuan'}</Link>}
    {detail.can_delete_draft && <DraftDeleteAction id={detail.id} name={detail.policy_holder.full_name} done={async () => onDeleted()} />}
    {detail.status === 'ACTIVE' && <PdfDownload id={detail.id} />}
    {detail.status === 'SUBMITTED' && role === 'AGENT' && <a className="download" href="#inspection"><ScanSearch size={18} aria-hidden="true" />Tinjau pengajuan</a>}
    {detail.status === 'SUBMITTED' && (role === 'ADMIN' || role === 'SUPER_ADMIN') && <Link className="download" to={`/review/${detail.id}`} state={{ backTo }}><ShieldCheck size={18} aria-hidden="true" />Verifikasi pengajuan</Link>}
  </>
}
