import { Link } from 'react-router-dom'
import { useResource } from '../hooks/useResource'
import type { AssuranceRow } from '../types/assurance'
import { Feedback } from '../components/shared/Feedback'
import { statusLabels } from '../utils/statusLabels'

export function DashboardPage() {
  const resource = useResource<AssuranceRow[]>('assurances/')
  return <section aria-busy={resource.loading}>
    <p className="eyebrow">Operasional</p><h1>Ringkasan</h1>
    <p>Jumlah berdasarkan data yang berhasil dimuat dari server dalam lingkup akun saat ini. Muat ulang untuk memperbarui; bukan pemantauan langsung.</p>
    <Feedback {...resource} retry={resource.reload} />
    {resource.data && <><p className="panel">Total data dimuat: <strong>{resource.data.length}</strong></p><div className="metrics">{Object.entries(statusLabels).map(([status, label]) => <Link className="panel metric" key={status} to={`/?status=${status}`}><span>{label}</span><strong>{resource.data?.filter(row => row.status === status).length}</strong></Link>)}</div><button className="secondary" onClick={() => void resource.reload()}>Muat ulang ringkasan</button></>}
  </section>
}
