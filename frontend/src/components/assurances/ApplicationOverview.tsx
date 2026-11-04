import type { ReactNode } from 'react'
import type { AssuranceDetail } from '../../types/assurance'
import { StatusBadge } from '../shared/StatusBadge'

export function ApplicationOverview({ detail, children }: { detail: AssuranceDetail; children?: ReactNode }) {
  const correction = detail.status === 'REVISION'
  return <section className="panel application-overview" aria-label="Ringkasan pengajuan">
    <div className="record-heading"><h2>{detail.policy_holder.full_name}</h2><StatusBadge status={detail.status} stage={detail.verification_stage} /></div>
    <p>{detail.dealer.name} · {detail.assurance_number ?? 'Nomor jaminan belum diterbitkan'}</p>
    {correction && <p>Perbaiki bagian yang diminta, lalu kirim ulang pengajuan untuk diperiksa kembali.</p>}
    {detail.status === 'REJECTED' && <p>Pengajuan ditolak final dan tidak dapat diedit atau dikirim ulang.</p>}
    {children && <div className="actions application-actions">{children}</div>}
    {(correction || detail.status === 'REJECTED') && detail.review_notes && <p className="notice"><strong>{correction ? 'Perbaikan yang diminta:' : 'Alasan penolakan:'}</strong> {detail.review_notes}</p>}
  </section>
}
