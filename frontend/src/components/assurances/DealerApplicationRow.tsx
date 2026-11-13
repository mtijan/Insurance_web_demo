import { Link } from 'react-router-dom'
import { AlertCircle, Eye, FilePenLine } from 'lucide-react'
import type { AssuranceRow } from '../../types/assurance'
import { StatusBadge } from '../shared/StatusBadge'
import { workflowStage, verificationLabel } from '../../utils/workflowPresentation'
import { money, dateLabel } from '../../utils/format'

export function DealerApplicationRow({ row }: { row: AssuranceRow }) {
  const draft = row.status === 'DRAFT'
  const Icon = draft ? FilePenLine : row.status === 'REVISION' ? AlertCircle : Eye
  const actionLabel = draft ? 'Buka draft' : row.status === 'REVISION' ? 'Lihat catatan perbaikan' : 'Lihat tahap pengajuan'
  return <li>
    <div className="record-cell-main"><div className="record-heading"><Link to={`/assurances/${row.id}`}>{row.policy_holder_name}</Link></div><p className="application-stage">Tahap: <strong>{workflowStage(row.status, row.verification_stage)}</strong></p></div>
    <div className="record-cell-main">{row.assurance_number ? <span className="code-badge">{row.assurance_number}</span> : <span className="record-cell-sub">Nomor jaminan belum diterbitkan</span>}<span className="record-cell-sub">Dibuat {dateLabel(row.created_at)}</span></div>
    <div className="record-cell-money">{money(row.total_premium)}</div>
    <div className="record-cell-status"><StatusBadge status={row.status} stage={row.verification_stage} />{!draft && <div className="dealer-stage-flags"><span>Data: {verificationLabel(row.status, row.data_verified)}</span><span>Berkas: {verificationLabel(row.status, row.documents_verified)}</span></div>}</div>
    <div className="record-actions"><Link className="back-link" to={draft ? `/assurances/${row.id}/edit` : `/assurances/${row.id}`}><Icon size={16} aria-hidden="true" />{actionLabel}</Link></div>
  </li>
}
