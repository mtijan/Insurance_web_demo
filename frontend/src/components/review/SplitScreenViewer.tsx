import type { AssuranceDetail } from '../../types/assurance'
import { AssuranceSummary } from '../assurances/AssuranceSummary'
import { DocumentViewer } from './DocumentViewer'

export function SplitScreenViewer({ detail }: { detail: AssuranceDetail }) {
  return <div className="review-workspace"><AssuranceSummary detail={detail} /><DocumentViewer id={detail.id} documents={detail.documents} /></div>
}
