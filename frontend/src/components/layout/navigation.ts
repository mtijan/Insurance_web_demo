import { LayoutDashboard, List, FilePlus, ScanSearch, Store, Users, Network, FileSpreadsheet, Settings, History } from 'lucide-react'
import type { Role } from '../../types/auth'

const all: Role[] = ['SUPER_ADMIN', 'ADMIN', 'AGENT', 'DEALER']
const reviewers: Role[] = ['SUPER_ADMIN', 'ADMIN']
const owner: Role[] = ['SUPER_ADMIN']
export const navigation = [
  { group: 'Operasional', label: 'Ringkasan', to: '/dashboard', icon: LayoutDashboard, roles: all, ready: true },
  { group: 'Operasional', label: 'Daftar jaminan', to: '/', icon: List, roles: all, ready: true },
  { group: 'Operasional', label: 'Buat pengajuan', to: '/assurances/new', icon: FilePlus, roles: all, ready: true },
  { group: 'Operasional', label: 'Verifikasi', to: '/review', icon: ScanSearch, roles: reviewers, ready: true },
  { group: 'Master data', label: 'Dealer', to: '/dealers', icon: Store, roles: all, ready: true },
  { group: 'Master data', label: 'Pengguna', to: '/admin/users', icon: Users, roles: owner, ready: true },
  { group: 'Master data', label: 'Penugasan agent', to: '/admin/assignments', icon: Network, roles: owner, ready: true },
  { group: 'Administrasi', label: 'Laporan Excel', to: '/admin/reports', icon: FileSpreadsheet, roles: owner, ready: true },
  { group: 'Administrasi', label: 'Biaya admin', to: '/admin/settings/admin-fee', icon: Settings, roles: owner, ready: true },
  { group: 'Administrasi', label: 'Riwayat audit', to: '/audit', icon: History, roles: owner, ready: true },
]
