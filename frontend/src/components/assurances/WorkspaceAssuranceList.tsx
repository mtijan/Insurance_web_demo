import { Link } from 'react-router-dom'
import { Eye, FilePlus } from 'lucide-react'
import type { AssuranceRow } from '../../types/assurance'
import type { Dealer } from '../../types/dealer'
import type { Role } from '../../types/auth'
import { Feedback } from '../shared/Feedback'
import { StatusBadge } from '../shared/StatusBadge'
import { IconAction } from '../shared/IconAction'
import { AssuranceFilters } from './AssuranceFilters'
import { DraftDeleteAction } from './DraftDeleteAction'
import { money } from '../../utils/format'
import { workflowStage } from '../../utils/workflowPresentation'

interface Props {
  role?: Role
  selected?: Dealer
  invalid: boolean
  backTo: string
  hasFilter: boolean
  assurances: { data?: AssuranceRow[]; error: string; loading: boolean; reload: () => Promise<unknown> }
}

function assuranceLink(row: AssuranceRow, role?: Role) {
  return role === 'ADMIN' && row.status === 'SUBMITTED' ? `/review/${row.id}` : `/assurances/${row.id}`
}

export function WorkspaceAssuranceList({ role, selected, invalid, backTo, hasFilter, assurances }: Props) {
  if (invalid) return <div role="alert" className="notice">Dealer yang dipilih tidak tersedia atau tidak lagi berada dalam lingkup akun Anda. Pilih dealer lain dari daftar.</div>
  if (!selected) return <div className="panel"><h2>Daftar jaminan dealer</h2><p>Pilih salah satu dealer untuk melihat daftar jaminan atau membuat pengajuan baru.</p></div>
  const rows = assurances.data ?? []
  return <section className="workspace-assurances" aria-label={`Jaminan ${selected.name}`} aria-busy={assurances.loading}>
    <WorkspaceSelectedBar selected={selected} backTo={backTo} />
    <AssuranceFilters hideDealer />
    <Feedback {...assurances} retry={assurances.reload} />
    {assurances.data && !rows.length && <WorkspaceEmpty hasFilter={hasFilter} />}
    {!!rows.length && <div className="record-table-card">
      <div className="record-table-head" aria-hidden="true"><span>Tertanggung</span><span>Nomor jaminan</span><span>Total premi</span><span>Status & tahap</span><span>Aksi</span></div>
      <ul className="assurance-list">{rows.map(row => <WorkspaceRow key={row.id} row={row} role={role} backTo={backTo} reload={assurances.reload} />)}</ul>
    </div>}
    {assurances.data && <p className="muted">{rows.length} pengajuan dimuat untuk dealer terpilih.</p>}
  </section>
}

function WorkspaceSelectedBar({ selected, backTo }: { selected: Dealer; backTo: string }) {
  return <div className="panel workspace-selected-bar">
    <div><span className="code-badge">{selected.code}</span><h2>{selected.name}</h2></div>
    {selected.is_active ? <Link className="download" to={`/assurances/new?dealer=${selected.id}`} state={{ backTo }}><FilePlus size={18} aria-hidden="true" />Buat pengajuan</Link> : <span className="badge status-INACTIVE">Dealer nonaktif</span>}
  </div>
}

function WorkspaceEmpty({ hasFilter }: { hasFilter: boolean }) {
  return <div className="panel"><h2>{hasFilter ? 'Tidak ada jaminan dengan filter ini' : 'Belum ada pengajuan pada dealer ini'}</h2><p>{hasFilter ? 'Ubah atau hapus filter untuk melihat data lain.' : 'Gunakan tombol Buat pengajuan untuk memulai pengajuan baru pada dealer ini.'}</p></div>
}

function WorkspaceRow({ row, role, backTo, reload }: { row: AssuranceRow; role?: Role; backTo: string; reload: () => Promise<unknown> }) {
  const target = assuranceLink(row, role)
  return <li>
    <div className="record-cell-main"><div className="record-heading"><Link to={target} state={{ backTo }}>{row.policy_holder_name}</Link></div></div>
    <div>{row.assurance_number ? <span className="code-badge">{row.assurance_number}</span> : <span className="record-cell-sub">Nomor belum diterbitkan</span>}</div>
    <div className="record-cell-money">{money(row.total_premium)}</div>
    <div className="record-cell-status"><StatusBadge status={row.status} stage={row.verification_stage} /><span className="record-cell-sub">{workflowStage(row.status, row.verification_stage)}</span></div>
    <div className="record-actions"><IconAction label={`Buka detail ${row.policy_holder_name}`} icon={Eye} to={target} />{row.can_delete_draft && <DraftDeleteAction id={row.id} name={row.policy_holder_name} done={reload} />}</div>
  </li>
}
