import { useState } from 'react'
import type { Dealer } from '../../types/dealer'
import { dealerSchema, schemaMessage } from '../../schemas/master'
import { api } from '../../services/apiClient'
import { useOperation } from '../../hooks/useOperation'
import { Field } from '../shared/Field'
import { ConfirmDialog } from '../shared/ConfirmDialog'

export function DealerEditor({ initial, close, done }: { initial?: Dealer; close: () => void; done: () => Promise<unknown> }) {
  const [values, setValues] = useState(() => ({ code: initial?.code ?? '', name: initial?.name ?? '', address: initial?.address ?? '', phone: initial?.phone ?? '', is_active: initial?.is_active ?? true }))
  const [confirm, setConfirm] = useState(false), operation = useOperation()
  function update(key: keyof typeof values, value: string | boolean) { setValues(v => ({ ...v, [key]: value })) }
  async function save() {
    const parsed = dealerSchema.safeParse(values)
    if (!parsed.success) { operation.setError(schemaMessage(parsed.error)); return }
    if (!confirm) { setConfirm(true); return }
    const result = await operation.run(signal => initial ? api.patch(`dealers/${initial.id}/`, parsed.data, { signal }) : api.post('dealers/', parsed.data, { signal }))
    if (result.ok) { await done(); close() }
  }
  return <ConfirmDialog title={initial ? 'Ubah dealer' : 'Tambah dealer'} close={close} busy={operation.busy}>
    <form noValidate onSubmit={e => { e.preventDefault(); void save() }}><fieldset disabled={operation.busy || confirm} className="form-grid">
      <Field name="code" label="Kode dealer" value={values.code} maxLength={20} onChange={e => update('code', e.target.value)} />
      <Field name="name" label="Nama dealer" value={values.name} maxLength={100} onChange={e => update('name', e.target.value)} />
      <Field name="phone" label="Telepon dealer" type="tel" value={values.phone} maxLength={20} onChange={e => update('phone', e.target.value)} />
      <label>Alamat dealer<textarea value={values.address} onChange={e => update('address', e.target.value)} /></label>
      <label className="check-field"><input type="checkbox" checked={values.is_active} onChange={e => update('is_active', e.target.checked)} />Dealer aktif</label>
    </fieldset>{operation.error && <p role="alert" className="error">{operation.error}</p>}{confirm && <p className="notice">Simpan data dealer ini? Perubahan akan dicatat oleh server.</p>}
    {confirm && <button type="button" className="secondary" disabled={operation.busy} onClick={() => setConfirm(false)}>Koreksi isian</button>}<button disabled={operation.busy}>{confirm ? 'Konfirmasi simpan dealer' : 'Tinjau perubahan dealer'}</button></form>
  </ConfirmDialog>
}
