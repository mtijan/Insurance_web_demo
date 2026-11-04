import type { Role } from '../types/auth'

export function dealerTitle(role?: Role) {
  if (role === 'DEALER') return 'Profil dealer'
  if (role === 'AGENT') return 'Dealer binaan'
  return 'Dealer'
}
