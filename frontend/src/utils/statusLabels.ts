export const statusLabels: Record<string, string> = { DRAFT: 'Draft', SUBMITTED: 'Dalam pemeriksaan', REVISION: 'Perlu perbaikan', ACTIVE: 'Aktif', APPROVED: 'Disetujui (data terdahulu)', REJECTED: 'Ditolak final' }
export const progressStatuses = Object.keys(statusLabels).filter(status => status !== 'DRAFT')
