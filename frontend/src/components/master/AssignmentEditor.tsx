import { useState } from 'react'
import { z } from 'zod'
import type { Assignment, ManagedUser } from '../../types/master'
import type { Dealer } from '../../types/dealer'
import { api } from '../../services/apiClient'
import { useOperation } from '../../hooks/useOperation'
import { ConfirmDialog } from '../shared/ConfirmDialog'

export function AssignmentEditor({ initial, agents, dealers, close, done, preferredAgent = '' }: { initial?: Assignment; agents: ManagedUser[]; dealers: Dealer[]; close: () => void; done: () => Promise<unknown>; preferredAgent?: string }) {
  const [agent, setAgent] = useState(initial?.agent ?? preferredAgent), [dealer, setDealer] = useState(initial?.dealer ?? '')
  const [confirm, setConfirm] = useState(false), operation = useOperation()
  async function save() {
    if (!z.uuid().safeParse(agent).success || !z.uuid().safeParse(dealer).success) { operation.setError('Pilih Agent dan Dealer yang sah.'); return }
    if (!confirm) { setConfirm(true); return }
    const result = await operation.run(signal => initial ? api.patch(`dealers/assignments/${initial.id}/`, { agent, dealer }, { signal }) : api.post('dealers/assignments/', { agent, dealer }, { signal }))
    if (result.ok) { await done(); close() }
  }
  return <ConfirmDialog title={initial ? 'Ubah penugasan agent' : 'Tambah penugasan agent'} close={close} busy={operation.busy}>
    <form noValidate onSubmit={e => { e.preventDefault(); void save() }}><fieldset disabled={operation.busy || confirm}>
      <label><span id="assignment-agent">Agent</span><select aria-labelledby="assignment-agent" value={agent} onChange={e => setAgent(e.target.value)}><option value="">Pilih Agent</option>{agents.map(a => <option value={a.id} key={a.id}>{a.username}{!a.is_active && ' (nonaktif)'}</option>)}</select></label>
      <label><span id="assignment-dealer">Dealer penugasan</span><select aria-labelledby="assignment-dealer" value={dealer} onChange={e => setDealer(e.target.value)}><option value="">Pilih Dealer</option>{dealers.map(d => <option value={d.id} key={d.id}>{d.name}{!d.is_active && ' (nonaktif)'}</option>)}</select></label>
    </fieldset>{operation.error && <p role="alert" className="error">{operation.error}</p>}{confirm && <p className="notice">Penugasan mengubah lingkup baca Agent untuk dealer ini. Simpan perubahan?</p>}
      {confirm && <button className="secondary" type="button" disabled={operation.busy} onClick={() => setConfirm(false)}>Koreksi isian</button>}<button disabled={operation.busy}>{confirm ? 'Konfirmasi simpan penugasan' : 'Tinjau penugasan'}</button>
    </form>
  </ConfirmDialog>
}
