import type { Role } from '../types/auth'

export function dealerTitle(role?: Role) {
  if (role === 'DEALER') return 'Profil dealer'
  if (role === 'AGENT') return 'Dealer binaan'
  if (role === 'ADMIN') return 'Dealer & jaminan'
  return 'Dealer'
}

export function isWorkspaceRole(role?: Role) {
  return role === 'AGENT' || role === 'ADMIN'
}

export function assuranceReturnPath(role?: Role, dealerId?: string, status?: string) {
  if (role === 'DEALER') return status === 'DRAFT' ? '/assurances/drafts' : '/assurances/progress'
  if (isWorkspaceRole(role)) return dealerId ? `/dealers?dealer=${dealerId}` : '/dealers'
  return '/'
}

export function assuranceReturnLabel(role?: Role) {
  if (role === 'DEALER') return 'Kembali ke daftar pengajuan'
  if (role === 'AGENT') return 'Kembali ke dealer binaan'
  if (role === 'ADMIN') return 'Kembali ke dealer & jaminan'
  return 'Kembali ke daftar jaminan'
}

export function safeBackTarget(state: unknown, fallback: string) {
  const candidate = (state as { backTo?: unknown } | null)?.backTo
  return typeof candidate === 'string' && candidate.startsWith('/') ? candidate : fallback
}
