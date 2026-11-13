import { useSearchParams } from 'react-router-dom'
import { FilterX } from 'lucide-react'
import { useResource } from '../../hooks/useResource'
import type { Dealer } from '../../types/dealer'
import { statusLabels } from '../../utils/statusLabels'
import { IconAction } from '../shared/IconAction'

function clearFilters(params: URLSearchParams, defaultStatus: string, hideDealer: boolean) {
  const next = new URLSearchParams()
  if (!hideDealer && defaultStatus) next.set('status', '')
  const dealer = hideDealer ? params.get('dealer') ?? params.get('dealer_id') : null
  if (dealer) next.set('dealer', dealer)
  return next
}

function DealerSelect({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  const dealers = useResource<Dealer[]>('dealers/?summary=true')
  return <>
    <label><span id="filter-dealer-label">Dealer</span>
      <select aria-labelledby="filter-dealer-label" name="dealer_id" disabled={!dealers.data} value={value} onChange={e => onChange(e.target.value)}>
        <option value="">Semua dealer dalam lingkup</option>
        {dealers.data?.map(dealer => <option key={dealer.id} value={dealer.id}>{dealer.name}</option>)}
      </select>
    </label>
    {dealers.error && <p className="error">Pilihan dealer gagal dimuat. <button onClick={() => void dealers.reload()}>Muat ulang dealer</button></p>}
  </>
}

export function AssuranceFilters({ dates = false, defaultStatus = '', tasks = false, hideDealer = false }: { dates?: boolean; defaultStatus?: string; tasks?: boolean; hideDealer?: boolean }) {
  const [params, setParams] = useSearchParams()
  function change(key: string, value: string) {
    const next = new URLSearchParams(params)
    if (value || (key === 'status' && defaultStatus)) next.set(key, value); else next.delete(key)
    if (key === 'task' && value) next.set('status', 'SUBMITTED')
    if (key === 'status' && value !== 'SUBMITTED') next.delete('task')
    setParams(next)
  }
  return <div className="filters panel">
    {tasks && <label>Tugas pemeriksaan<select value={params.get('task') ?? ''} onChange={e => change('task', e.target.value)}><option value="">Semua tugas</option><option value="verify">Perlu verifikasi data/berkas</option><option value="decision">Menunggu keputusan</option></select></label>}
    <label><span id="filter-status-label">Status</span><select aria-labelledby="filter-status-label" name="status" value={params.get('status') ?? defaultStatus} onChange={e => change('status', e.target.value)}><option value="">Semua status</option>{Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    {!hideDealer && <DealerSelect value={params.get('dealer_id') ?? ''} onChange={value => change('dealer_id', value)} />}
    {dates && <><label>Dibuat mulai (WIB)<input type="date" value={params.get('date_from') ?? ''} onChange={e => change('date_from', e.target.value)} /></label><label>Dibuat sampai (WIB)<input type="date" value={params.get('date_to') ?? ''} onChange={e => change('date_to', e.target.value)} /></label></>}
    <IconAction label="Hapus filter" icon={FilterX} onClick={() => setParams(clearFilters(params, defaultStatus, hideDealer))} />
  </div>
}
