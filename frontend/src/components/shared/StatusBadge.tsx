import { workflowLabel } from '../../utils/workflowPresentation'
export function StatusBadge({ status, stage }: { status: string; stage?: string }) { return <span className={`badge status-${status}`}>{workflowLabel(status, stage)}</span> }
