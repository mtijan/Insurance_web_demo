import { Link, useParams } from 'react-router-dom'
import { useResource } from '../hooks/useResource'
import type { AssuranceDetail } from '../types/assurance'
import { Feedback } from '../components/shared/Feedback'
import { SplitScreenViewer } from '../components/review/SplitScreenViewer'
import { ReviewActions } from '../components/review/ReviewActions'
import { useReviewDecision } from '../hooks/useReviewDecision'
import { ReviewProgress } from '../components/review/ReviewProgress'
import { InspectionPanel } from '../components/review/InspectionPanel'
import { useInspection } from '../hooks/useInspection'
import { ApplicationOverview } from '../components/assurances/ApplicationOverview'
import { ReviewHistory } from '../components/review/ReviewHistory'

export function AdminReviewPage() {
  const { id } = useParams()
  return <ReviewWorkspace key={id} id={id!} />
}
function ReviewWorkspace({ id }: { id: string }) {
  const resource = useResource<AssuranceDetail>(`assurances/${id}/`)
  const review = useReviewDecision(id, resource.reload)
  const inspection = useInspection(id, resource.reload)
  return <section aria-busy={resource.loading}><Link to="/review">Kembali ke antrean verifikasi</Link><h1>Verifikasi pengajuan</h1>
    <Feedback {...resource} retry={resource.reload} />
    {review.success && <p role="status" className="notice">{review.success}</p>}
    {inspection.success && <p role="status">{inspection.success}</p>}
    {resource.data && <><ApplicationOverview detail={resource.data} />
      {resource.data.status === 'SUBMITTED' && <ReviewActions review={review} />}
      <ReviewProgress detail={resource.data} /><SplitScreenViewer detail={resource.data} />
      {resource.data.status === 'SUBMITTED' ? <InspectionPanel detail={resource.data} admin review={inspection} /> : <p className="notice">Keputusan hanya dapat dibuat ketika pengajuan sedang diajukan. Status saat ini: {resource.data.status}.</p>}
      <ReviewHistory detail={resource.data} /></>}
  </section>
}
