import { Link } from 'react-router-dom'
import { useResource } from '../hooks/useResource'
import type { AssuranceRow } from '../types/assurance'
import { Feedback } from '../components/shared/Feedback'
import { statusLabels } from '../utils/statusLabels'
import { useAuth } from '../auth/authState'
import { dashboardTasks, isTask } from '../utils/dashboardTasks'

export function DashboardPage() {
  const resource = useResource<AssuranceRow[]>('assurances/')
  const { user } = useAuth()
  const rows = resource.data ?? []
  const tasks = user ? dashboardTasks(user.role) : []
  return <section aria-busy={resource.loading}>
    <div className="page-heading"><div><p className="eyebrow">Operasional</p><h1>Ringkasan</h1></div><button className="secondary" onClick={() => void resource.reload()}>Muat ulang ringkasan</button></div>
    <p>Prioritas pekerjaan dan ringkasan pengajuan dalam lingkup akun Anda.</p>
    <Feedback {...resource} retry={resource.reload} />
    {resource.data && <><section aria-label="Prioritas pekerjaan"><h2>Perlu ditindaklanjuti</h2><div className="metrics task-metrics">{tasks.map(task => <Link className="panel metric" key={task.label} to={task.to}><span>{task.label}</span><strong>{rows.filter(row => row.status === task.status && isTask(row, task.task)).length}</strong></Link>)}</div></section>
      <div className="section-heading"><h2>Seluruh pengajuan</h2><p className="badge">Total data dimuat: <strong>{rows.length}</strong></p></div><div className="metrics">{['DRAFT', 'SUBMITTED', 'REVISION', 'ACTIVE', 'REJECTED'].map(status => <Link className={`panel metric metric-${status}`} key={status} to={`/?status=${status}`}><span>{statusLabels[status]}</span><strong>{rows.filter(row => row.status === status).length}</strong></Link>)}</div>
      {!!rows.filter(row => row.status === 'APPROVED').length && <p>Data persetujuan terdahulu: {rows.filter(row => row.status === 'APPROVED').length}.</p>}
      <p className="muted">Jumlah berdasarkan data yang berhasil dimuat. Muat ulang untuk memperbarui.</p></>}
  </section>
}
