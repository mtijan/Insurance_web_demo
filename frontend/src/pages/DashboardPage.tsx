import { Link } from 'react-router-dom'
import { AlertCircle, Clock, Eye, FilePenLine, Layers, RefreshCw, ShieldCheck, XCircle } from 'lucide-react'
import { useResource } from '../hooks/useResource'
import type { AssuranceRow } from '../types/assurance'
import { Feedback } from '../components/shared/Feedback'
import { DataTable } from '../components/shared/DataTable'
import { StatusBadge } from '../components/shared/StatusBadge'
import { IconAction } from '../components/shared/IconAction'
import { statusLabels } from '../utils/statusLabels'
import { money } from '../utils/format'
import { useAuth } from '../auth/authState'
import { dashboardTasks, isTask } from '../utils/dashboardTasks'

const statusIcons = {
  DRAFT: FilePenLine,
  SUBMITTED: Clock,
  REVISION: AlertCircle,
  ACTIVE: ShieldCheck,
  REJECTED: XCircle,
} as const

export function DashboardPage() {
  const resource = useResource<AssuranceRow[]>('assurances/')
  const { user } = useAuth()
  const rows = resource.data ?? []
  const tasks = user ? dashboardTasks(user.role) : []
  return <section aria-busy={resource.loading}>
    <div className="page-heading"><div><p className="eyebrow">Operasional</p><h1>Ringkasan</h1></div><button className="secondary" onClick={() => void resource.reload()}><RefreshCw size={16} aria-hidden="true" />Muat ulang ringkasan</button></div>
    <p>Prioritas pekerjaan dan ringkasan pengajuan dalam lingkup akun Anda.</p>
    <Feedback {...resource} retry={resource.reload} />
    {resource.data && <>
      <section aria-label="Prioritas pekerjaan"><h2>Perlu ditindaklanjuti</h2><div className="metrics task-metrics">{tasks.map(task => {
        const Icon = task.status === 'REVISION' ? AlertCircle : task.status === 'DRAFT' ? FilePenLine : Clock
        return <Link className="panel metric" key={task.label} to={task.to}><div className="metric-top"><span>{task.label}</span><span className="metric-icon" aria-hidden="true"><Icon size={18} /></span></div><strong>{rows.filter(row => row.status === task.status && isTask(row, task.task)).length}</strong></Link>
      })}</div></section>
      <div className="section-heading"><h2>Seluruh pengajuan</h2><p className="badge"><Layers size={14} aria-hidden="true" />Total data dimuat: <strong>{rows.length}</strong></p></div>
      <div className="metrics">{(['DRAFT', 'SUBMITTED', 'REVISION', 'ACTIVE', 'REJECTED'] as const).map(status => {
        const Icon = statusIcons[status]
        return <Link className={`panel metric metric-${status}`} key={status} to={`/?status=${status}`}><div className="metric-top"><span>{statusLabels[status]}</span><span className="metric-icon" aria-hidden="true"><Icon size={18} /></span></div><strong>{rows.filter(row => row.status === status).length}</strong></Link>
      })}</div>
      {!!rows.length && <RecentAssurancesTable rows={rows.slice(0, 5)} role={user?.role} />}
      {!!rows.filter(row => row.status === 'APPROVED').length && <p>Data persetujuan terdahulu: {rows.filter(row => row.status === 'APPROVED').length}.</p>}
      <p className="muted">Jumlah berdasarkan data yang berhasil dimuat. Muat ulang untuk memperbarui.</p>
    </>}
  </section>
}

function RecentAssurancesTable({ rows, role }: { rows: AssuranceRow[]; role?: string }) {
  return <>
    <div className="section-heading"><h2>Pengajuan terbaru</h2>{role === 'SUPER_ADMIN' && <Link to="/">Lihat semua jaminan</Link>}</div>
    <DataTable rows={rows} label="Pengajuan terbaru" columns={[
      { label: 'Tertanggung', render: row => <Link to={role === 'ADMIN' && row.status === 'SUBMITTED' ? `/review/${row.id}` : `/assurances/${row.id}`}>{row.policy_holder_name}</Link> },
      { label: 'Dealer', render: row => row.dealer_name },
      { label: 'Nomor jaminan', render: row => row.assurance_number ? <span className="code-badge">{row.assurance_number}</span> : <span className="muted">Belum diterbitkan</span> },
      { label: 'Total premi', render: row => money(row.total_premium) },
      { label: 'Status', render: row => <StatusBadge status={row.status} stage={row.verification_stage} /> },
      { label: 'Aksi', render: row => <div className="actions"><IconAction label={`Lihat detail ${row.policy_holder_name}`} icon={Eye} to={role === 'ADMIN' && row.status === 'SUBMITTED' ? `/review/${row.id}` : `/assurances/${row.id}`} /></div> },
    ]} />
  </>
}
