import { Link, useSearchParams } from 'react-router-dom'
import { useResource } from '../hooks/useResource'
import type { AssuranceRow } from '../types/assurance'
import { Feedback } from '../components/shared/Feedback'
import { StatusBadge } from '../components/shared/StatusBadge'
import { AssuranceFilters } from '../components/assurances/AssuranceFilters'
import { money } from '../utils/format'
import { workflowStage } from '../utils/workflowPresentation'
import { isTask } from '../utils/dashboardTasks'

export function AssurancesPage({ review = false, inspection = false }: { review?: boolean; inspection?: boolean }) {
  const [params] = useSearchParams()
  const mode = listMode(review, inspection)
  const query = new URLSearchParams(params)
  query.delete('task')
  if (mode.defaultStatus && !params.has('status')) query.set('status', mode.defaultStatus)
  const resource = useResource<AssuranceRow[]>(`assurances/?${query}`)
  const rows = (resource.data ?? []).filter(row => isTask(row, params.get('task')))
  return <section aria-busy={resource.loading}>
    <div className="page-heading"><div><p className="eyebrow">Operasional</p><h1>{mode.title}</h1></div></div>
    <p>{mode.intro}</p>
    <AssuranceFilters defaultStatus={mode.defaultStatus} tasks={review} />
    <Feedback {...resource} retry={resource.reload} />
    <EmptyList loaded={!!resource.data} count={rows.length} filtered={!!params.size || !!mode.defaultStatus} />
    <ul className="assurance-list">{rows.map(row => <li key={row.id}>
      <div className="record-heading"><Link to={review ? `/review/${row.id}` : `/assurances/${row.id}`}>{row.policy_holder_name}</Link><StatusBadge status={row.status} stage={row.verification_stage} /></div>
      <span>Dealer: {row.dealer_name}</span><span>{row.assurance_number ?? 'Nomor belum diterbitkan'}</span><span>Total premi: {money(row.total_premium)}</span>
      <span>Tahap pemeriksaan: {workflowStage(row.status, row.verification_stage)}</span>
    </li>)}</ul>
    {resource.data && <p className="muted">{rows.length} pengajuan dimuat untuk filter dan lingkup akun saat ini.</p>}
  </section>
}
function listMode(review: boolean, inspection: boolean) {
  if (review) return { title: 'Antrean verifikasi', intro: 'Periksa pengajuan, minta perbaikan bila diperlukan, lalu ambil keputusan.', defaultStatus: 'SUBMITTED' }
  if (inspection) return { title: 'Peninjauan pengajuan', intro: 'Tinjau pengajuan dealer binaan dan catat bagian yang perlu diperbaiki.', defaultStatus: 'SUBMITTED' }
  return { title: 'Daftar jaminan', intro: 'Pantau pengajuan, buka detail, atau lanjutkan pengajuan yang perlu diperbaiki.', defaultStatus: '' }
}

function EmptyList({ loaded, count, filtered }: { loaded: boolean; count: number; filtered: boolean }) {
  if (!loaded || count) return null
  return <div className="panel"><h2>{filtered ? 'Tidak ada jaminan dengan filter ini' : 'Belum ada jaminan dalam lingkup akun Anda'}</h2><p>{filtered ? 'Ubah atau hapus filter untuk melihat data lain.' : 'Belum ada data pada lingkup ini.'}</p></div>
}
