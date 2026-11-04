import { useState } from 'react'
import { feeSchema, schemaMessage } from '../../schemas/master'
import { api } from '../../services/apiClient'
import { useOperation } from '../../hooks/useOperation'
import { Field } from '../shared/Field'
import { ConfirmDialog } from '../shared/ConfirmDialog'
import { money } from '../../utils/format'

export function AdminFeeConfigModal({ value, close, done }: { value: string; close: () => void; done: () => Promise<unknown> }) {
  const [amount, setAmount] = useState(value), [reason, setReason] = useState(''), [confirm, setConfirm] = useState(false)
  const operation = useOperation()
  async function save() {
    const valid = feeSchema.safeParse({ admin_fee: amount, reason })
    if (!valid.success) { operation.setError(schemaMessage(valid.error)); return }
    if (!confirm) { setConfirm(true); return }
    const result = await operation.run(signal => api.put('configs/admin-fee/', valid.data, { signal }))
    if (result.ok) { await done(); close() }
  }
  return <ConfirmDialog title="Ubah biaya admin" close={close} busy={operation.busy}><form noValidate onSubmit={e => { e.preventDefault(); void save() }}>
    <fieldset disabled={operation.busy || confirm}><Field name="admin_fee" label="Biaya admin baru (Rp)" inputMode="decimal" value={amount} onChange={e => setAmount(e.target.value)} />
      <label>Alasan perubahan (wajib)<textarea required maxLength={1000} value={reason} onChange={e => setReason(e.target.value)} /></label></fieldset>
    <p>Nilai baru berlaku untuk draft baru dan simulasi. Biaya snapshot transaksi existing tidak dihitung ulang.</p>
    {operation.error && <p role="alert" className="error">{operation.error}</p>}
    {confirm && <p className="notice">Ubah biaya admin dari {money(value)} menjadi {money(amount)}?</p>}
    {confirm && <button className="secondary" type="button" disabled={operation.busy} onClick={() => setConfirm(false)}>Koreksi isian</button>}<button disabled={operation.busy}>{confirm ? 'Konfirmasi biaya admin' : 'Tinjau biaya admin'}</button>
  </form></ConfirmDialog>
}
