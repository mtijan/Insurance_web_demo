import { workflowLabel } from '../../utils/workflowPresentation'

export function StatusBadge({ status, stage }: { status: string; stage?: string }) {
  return <span className={`badge status-${status}`}><span className="status-dot" aria-hidden="true" />{workflowLabel(status, stage)}</span>
}
