import { useSearchParams } from 'react-router-dom'
import { statusLabels, progressStatuses } from '../../utils/statusLabels'
import { FilterX } from 'lucide-react'
import { IconAction } from '../shared/IconAction'

export function DealerApplicationFilters() {
  const [params, setParams] = useSearchParams()
  const status = params.get('status') ?? ''
  return <div className="filters panel">
    <label><span id="dealer-progress-status-label">Status pengajuan</span><select id="dealer-progress-status" aria-labelledby="dealer-progress-status-label" value={progressStatuses.includes(status) ? status : ''} onChange={event => setParams(event.target.value ? { status: event.target.value } : {})}>
      <option value="">Semua status pengajuan</option>{progressStatuses.map(value => <option key={value} value={value}>{statusLabels[value]}</option>)}
    </select></label>
    <IconAction label="Hapus filter" icon={FilterX} onClick={() => setParams({})} />
  </div>
}
