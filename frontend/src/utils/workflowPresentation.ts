export function workflowStage(status: string, stage = 'WAITING') {
  if (status === 'REVISION') return 'Menunggu perbaikan Dealer'
  if (status === 'ACTIVE') return 'Disetujui dan aktif'
  if (status === 'REJECTED') return 'Ditolak final'
  if (status === 'DRAFT') return 'Belum dikirim'
  if (stage === 'COMPLETE') return 'Menunggu keputusan Admin'
  if (stage === 'DOCUMENTS') return 'Verifikasi berkas'
  if (stage === 'DATA') return 'Verifikasi data'
  return 'Menunggu pemeriksaan'
}
export function workflowLabel(status: string, stage = 'WAITING') {
  if (status === 'SUBMITTED' && stage === 'COMPLETE') return 'Menunggu keputusan'
  if (status === 'SUBMITTED' && ['DATA', 'DOCUMENTS'].includes(stage)) return 'Sedang diverifikasi'
  const labels: Record<string, string> = { DRAFT: 'Draft', SUBMITTED: 'Menunggu verifikasi', REVISION: 'Perlu perbaikan', ACTIVE: 'Aktif', REJECTED: 'Ditolak final', APPROVED: 'Disetujui (data terdahulu)' }
  return labels[status] ?? status
}
export function verificationLabel(status: string, verified: boolean) {
  if (status === 'REVISION') return 'Perlu diperiksa ulang'
  return verified ? 'Terverifikasi' : 'Belum terverifikasi'
}
