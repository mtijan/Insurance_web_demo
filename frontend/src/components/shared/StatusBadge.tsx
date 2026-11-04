import { statusLabels } from '../../utils/statusLabels'
export function StatusBadge({ status }: { status: string }) { return <span className={`badge status-${status}`}>{statusLabels[status] ?? status}</span> }
