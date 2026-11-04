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
    {resource.data && <><SplitScreenViewer detail={resource.data} /><ReviewProgress detail={resource.data} />{resource.data.status === 'SUBMITTED' ? <><InspectionPanel detail={resource.data} admin review={inspection} /><ReviewActions review={review} /></> : <p className="notice">Status {resource.data.status}: keputusan tidak dapat diubah. Muat ulang untuk melihat status terbaru.</p>}</>}
  </section>
}
