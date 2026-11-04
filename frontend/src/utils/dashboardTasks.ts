import type { AssuranceRow } from '../types/assurance'
import type { Role } from '../types/auth'

export function isTask(row: AssuranceRow, task: string | null) {
  if (task === 'decision') return row.status === 'SUBMITTED' && row.verification_stage === 'COMPLETE'
  if (task === 'verify') return row.status === 'SUBMITTED' && row.verification_stage !== 'COMPLETE'
  return true
}
export function dashboardTasks(role: Role) {
  if (role === 'DEALER') return [
    { label: 'Perlu Anda perbaiki', to: '/?status=REVISION', status: 'REVISION', task: null },
    { label: 'Draft belum dikirim', to: '/?status=DRAFT', status: 'DRAFT', task: null },
  ]
  if (role === 'AGENT') return [
    { label: 'Pengajuan untuk ditinjau', to: '/inspection', status: 'SUBMITTED', task: null },
    { label: 'Menunggu perbaikan Dealer', to: '/?status=REVISION', status: 'REVISION', task: null },
  ]
  return [
    { label: 'Menunggu keputusan Anda', to: '/review?status=SUBMITTED&task=decision', status: 'SUBMITTED', task: 'decision' },
    { label: 'Perlu verifikasi data/berkas', to: '/review?status=SUBMITTED&task=verify', status: 'SUBMITTED', task: 'verify' },
  ]
}
