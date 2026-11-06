import { Link } from 'react-router-dom'
import type { AssuranceRow } from '../../types/assurance'
import { StatusBadge } from '../shared/StatusBadge'
import { workflowStage, verificationLabel } from '../../utils/workflowPresentation'
import { money, dateLabel } from '../../utils/format'

export function DealerApplicationRow({ row }: { row: AssuranceRow }) {
  const draft = row.status === 'DRAFT'
  return <li>
    <div className="record-heading"><Link to={`/assurances/${row.id}`}>{row.policy_holder_name}</Link><StatusBadge status={row.status} stage={row.verification_stage} /></div>
    <p className="application-stage">Tahap pengajuan: <strong>{workflowStage(row.status, row.verification_stage)}</strong></p>
    <span>{row.assurance_number ?? 'Nomor jaminan belum diterbitkan'}</span>
    <span>Total premi: {money(row.total_premium)} · Dibuat {dateLabel(row.created_at)}</span>
    {!draft && <div className="dealer-stage-flags"><span>Data: {verificationLabel(row.status, row.data_verified)}</span><span>Berkas: {verificationLabel(row.status, row.documents_verified)}</span></div>}
    <Link className="back-link" to={draft ? `/assurances/${row.id}/edit` : `/assurances/${row.id}`}>{draft ? 'Buka draft' : row.status === 'REVISION' ? 'Lihat catatan perbaikan' : 'Lihat tahap pengajuan'}</Link>
  </li>
}
