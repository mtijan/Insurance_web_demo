import { Link, useSearchParams } from 'react-router-dom'
import { useResource } from '../hooks/useResource'
import type { AssuranceRow } from '../types/assurance'
import { Feedback } from '../components/shared/Feedback'
import { StatusBadge } from '../components/shared/StatusBadge'
import { AssuranceFilters } from '../components/assurances/AssuranceFilters'
import { money } from '../utils/format'
import { stageLabels } from '../utils/reviewLabels'

export function AssurancesPage({ review = false }: { review?: boolean }) {
  const [params] = useSearchParams()
  const query = new URLSearchParams(params)
  if (review && !params.has('status')) query.set('status', 'SUBMITTED')
  const resource = useResource<AssuranceRow[]>(`assurances/?${query}`)
  const rows = resource.data ?? []
  return <section aria-busy={resource.loading}>
    <div className="page-heading"><div><p className="eyebrow">Operasional</p><h1>{review ? 'Antrean verifikasi' : 'Daftar jaminan'}</h1></div></div>
    <p>Data mengikuti lingkup akun di server. {review && 'Waktu SLA belum ditetapkan; tidak ada indikator SLA.'}</p>
    <AssuranceFilters defaultStatus={review ? 'SUBMITTED' : ''} />
    <Feedback {...resource} retry={resource.reload} />
    <EmptyList loaded={!!resource.data} count={rows.length} filtered={!!params.size || review} />
    <ul className="assurance-list">{rows.map(row => <li key={row.id}>
      <div className="record-heading"><Link to={review ? `/review/${row.id}` : `/assurances/${row.id}`}>{row.policy_holder_name}</Link><StatusBadge status={row.status} /></div>
      <span>Dealer: {row.dealer_name}</span><span>{row.assurance_number ?? 'Nomor belum diterbitkan'}</span><span>Total premi: {money(row.total_premium)}</span>
      <span>Tahap pemeriksaan: {stageLabels[row.verification_stage] ?? 'Belum diperiksa'}</span>
    </li>)}</ul>
    {resource.data && <p className="muted">{rows.length} pengajuan dimuat untuk filter dan lingkup akun saat ini.</p>}
  </section>
}

function EmptyList({ loaded, count, filtered }: { loaded: boolean; count: number; filtered: boolean }) {
  if (!loaded || count) return null
  return <div className="panel"><h2>{filtered ? 'Tidak ada jaminan dengan filter ini' : 'Belum ada jaminan dalam lingkup akun Anda'}</h2><p>{filtered ? 'Ubah atau hapus filter untuk melihat data lain.' : 'Belum ada data pada lingkup ini.'}</p></div>
}
