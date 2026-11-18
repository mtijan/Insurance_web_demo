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

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

export function isUuidParam(value?: string): value is string {
  return typeof value === 'string' && UUID_PATTERN.test(value)
}

function hasControlChar(value: string) {
  for (let index = 0; index < value.length; index++) {
    const code = value.charCodeAt(index)
    if (code < 32 || code === 127) return true
  }
  return false
}

const ROLE_NAMES: Record<string, string> = {
  SUPER_ADMIN: 'Super Admin',
  ADMIN: 'Admin Underwriting',
  AGENT: 'Agent',
  DEALER: 'Dealer Staff',
}

export function humanRoleLabel(role?: string) {
  if (!role) return 'Pengguna'
  return ROLE_NAMES[role] ?? role.replaceAll('_', ' ')
}

export function isSafeInternalPath(value: unknown): value is string {
  return typeof value === 'string' && value.startsWith('/') && !value.startsWith('//')
    && !value.includes('\\') && !hasControlChar(value)
}

export function formatJakartaTime(iso: string) {
  return `${new Date(iso).toLocaleString('id-ID', { timeZone: 'Asia/Jakarta' })} WIB`
}

export function safeBackTarget(state: unknown, fallback: string) {
  const candidate = (state as { backTo?: unknown } | null)?.backTo
  return isSafeInternalPath(candidate) ? candidate : fallback
}
