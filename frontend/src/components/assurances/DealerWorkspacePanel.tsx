import type { Dealer } from '../../types/dealer'
import { Feedback } from '../shared/Feedback'

interface Props {
  search: string
  onSearch: (value: string) => void
  dealers: { data?: Dealer[]; error: string; loading: boolean; reload: () => Promise<unknown> }
  filtered: Dealer[]
  selectedId?: string
  onSelect: (id: string) => void
}

export function DealerWorkspacePanel({ search, onSearch, dealers, filtered, selectedId, onSelect }: Props) {
  return <section className="panel workspace-dealers" aria-label="Pemilihan dealer" aria-busy={dealers.loading}>
    <h2>Pilih dealer</h2>
    <label htmlFor="workspace-dealer-search">Cari dealer
      <input id="workspace-dealer-search" type="search" placeholder="Cari kode atau nama dealer…" value={search} onChange={e => onSearch(e.target.value)} />
    </label>
    <Feedback {...dealers} retry={dealers.reload} />
    {dealers.data && !dealers.data.length && <p className="notice">Belum ada dealer dalam lingkup akun Anda.</p>}
    {!!dealers.data?.length && !filtered.length && <p className="muted">Tidak ada dealer yang cocok dengan pencarian.</p>}
    <ul className="dealer-picker-list">
      {filtered.map(dealer => <li key={dealer.id}>
        <button type="button" className={`dealer-option${dealer.id === selectedId ? ' active' : ''}`} aria-pressed={dealer.id === selectedId} onClick={() => onSelect(dealer.id)}>
          <span className="code-badge">{dealer.code}</span>
          <span className="dealer-option-name">{dealer.name}</span>
          <span className={`badge ${dealer.is_active ? 'status-ACTIVE' : 'status-INACTIVE'}`}><span className="status-dot" aria-hidden="true" />{dealer.is_active ? 'Aktif' : 'Nonaktif'}</span>
        </button>
      </li>)}
    </ul>
  </section>
}
