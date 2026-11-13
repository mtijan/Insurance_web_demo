import { useDealerWorkspace } from '../hooks/useDealerWorkspace'
import { DealerWorkspacePanel } from '../components/assurances/DealerWorkspacePanel'
import { WorkspaceAssuranceList } from '../components/assurances/WorkspaceAssuranceList'
import { dealerTitle } from '../utils/roleLabels'
import type { Role } from '../types/auth'

export function DealerWorkspacePage({ role }: { role: Role }) {
  const { params, search, setSearch, dealers, filteredDealers, selected, invalid, assurances, selectDealer } = useDealerWorkspace()
  const query = params.toString()
  const backTo = query ? `/dealers?${query}` : '/dealers'
  const hasFilter = Boolean(params.get('status') || params.get('date_from') || params.get('date_to'))
  return <section>
    <div className="page-heading"><div><p className="eyebrow">Operasional</p><h1>{dealerTitle(role)}</h1></div></div>
    <p>{role === 'AGENT' ? 'Pilih dealer binaan untuk melihat jaminan atau membuat pengajuan baru.' : 'Pilih dealer untuk memeriksa daftar jaminan atau membuat pengajuan baru.'}</p>
    <div className="workspace-grid">
      <DealerWorkspacePanel search={search} onSearch={setSearch} dealers={dealers} filtered={filteredDealers} selectedId={selected?.id} onSelect={selectDealer} />
      <WorkspaceAssuranceList role={role} selected={selected} invalid={invalid} backTo={backTo} hasFilter={hasFilter} assurances={assurances} />
    </div>
  </section>
}
