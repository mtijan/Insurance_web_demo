import { Link, useSearchParams } from 'react-router-dom'
import { Eye } from 'lucide-react'
import { useResource } from '../hooks/useResource'
import type { AssuranceRow } from '../types/assurance'
import { Feedback } from '../components/shared/Feedback'
import { StatusBadge } from '../components/shared/StatusBadge'
import { IconAction } from '../components/shared/IconAction'
import { AssuranceFilters } from '../components/assurances/AssuranceFilters'
import { DraftDeleteAction } from '../components/assurances/DraftDeleteAction'
import { money } from '../utils/format'
import { workflowStage } from '../utils/workflowPresentation'
import { isTask } from '../utils/dashboardTasks'

export function AssurancesPage({ review = false, inspection = false }: { review?: boolean; inspection?: boolean }) {
  const [params] = useSearchParams()
  const mode = listMode(review, inspection)
  const query = new URLSearchParams(params)
  query.delete('task')
  if (mode.defaultStatus && !params.has('status')) query.set('status', mode.defaultStatus)
  const resource = useResource<AssuranceRow[]>(query.size ? `assurances/?${query}` : 'assurances/')
  const rows = (resource.data ?? []).filter(row => isTask(row, params.get('task')))
  return <section aria-busy={resource.loading}>
    <div className="page-heading"><div><p className="eyebrow">Operasional</p><h1>{mode.title}</h1></div></div>
    <p>{mode.intro}</p>
    <AssuranceFilters defaultStatus={mode.defaultStatus} tasks={review} />
    <Feedback {...resource} retry={resource.reload} />
    <EmptyList loaded={!!resource.data} count={rows.length} filtered={!!params.size || !!mode.defaultStatus} />
    {!!rows.length && <div className="record-table-card">
      <div className="record-table-head" aria-hidden="true"><span>Tertanggung & dealer</span><span>Nomor jaminan</span><span>Total premi</span><span>Status & tahap</span><span>Aksi</span></div>
      <ul className="assurance-list">{rows.map(row => <AssuranceListItem key={row.id} row={row} review={review} reload={resource.reload} />)}</ul>
    </div>}
    {resource.data && <p className="muted">{rows.length} pengajuan dimuat untuk filter dan lingkup akun saat ini.</p>}
  </section>
}
function AssuranceListItem({ row, review, reload }: { row: AssuranceRow; review: boolean; reload: () => Promise<unknown> }) {
  const target = review ? `/review/${row.id}` : `/assurances/${row.id}`
  return <li>
    <div className="record-cell-main"><div className="record-heading"><Link to={target}>{row.policy_holder_name}</Link></div><span className="record-cell-sub">{row.dealer_name}</span></div>
    <div>{row.assurance_number ? <span className="code-badge">{row.assurance_number}</span> : <span className="record-cell-sub">Nomor belum diterbitkan</span>}</div>
    <div className="record-cell-money">{money(row.total_premium)}</div>
    <div className="record-cell-status"><StatusBadge status={row.status} stage={row.verification_stage} /><span className="record-cell-sub">{workflowStage(row.status, row.verification_stage)}</span></div>
    <div className="record-actions"><IconAction label={`${review ? 'Verifikasi' : 'Buka detail'} ${row.policy_holder_name}`} icon={Eye} to={target} />{row.can_delete_draft && <DraftDeleteAction id={row.id} name={row.policy_holder_name} done={reload} />}</div>
  </li>
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
