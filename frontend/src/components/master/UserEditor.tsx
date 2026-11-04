import { useState } from 'react'
import type { ManagedUser, UserFields as Values } from '../../types/master'
import type { Dealer } from '../../types/dealer'
import { userSchema, schemaMessage } from '../../schemas/master'
import { api } from '../../services/apiClient'
import { useOperation } from '../../hooks/useOperation'
import { ConfirmDialog } from '../shared/ConfirmDialog'
import { UserFields } from './UserFields'

export function UserEditor({ initial, dealers, close, done }: { initial?: ManagedUser; dealers: Dealer[]; close: () => void; done: () => Promise<unknown> }) {
  const [values, setValues] = useState<Values>(() => ({ username: initial?.username ?? '', email: initial?.email ?? '', first_name: initial?.first_name ?? '', last_name: initial?.last_name ?? '', role: initial?.role ?? 'AGENT', dealer: initial?.dealer ?? '', password: '', is_active: initial?.is_active ?? true }))
  const [confirm, setConfirm] = useState(false), operation = useOperation()
  function change(key: keyof Values, value: string | boolean) { setValues(v => ({ ...v, [key]: value })) }
  async function save() {
    const parsed = userSchema.safeParse(values)
    if (!parsed.success) { operation.setError(schemaMessage(parsed.error)); return }
    if (!confirm) { setConfirm(true); return }
    const { password, ...other } = parsed.data
    const payload = { ...other, dealer: other.dealer || null, ...(password ? { password } : {}) }
    const result = await operation.run(signal => initial ? api.patch(`auth/manage/${initial.id}/`, payload, { signal }) : api.post('auth/manage/', payload, { signal }))
    if (result.ok) { setValues(v => ({ ...v, password: '' })); await done(); close() }
  }
  return <ConfirmDialog title={initial ? 'Ubah pengguna' : 'Tambah pengguna'} close={close} busy={operation.busy}>
    <form noValidate onSubmit={e => { e.preventDefault(); void save() }}><fieldset disabled={operation.busy || confirm}><UserFields values={values} change={change} dealers={dealers} /></fieldset>
      {operation.error && <p role="alert" className="error">{operation.error}</p>}
      {confirm && <p className="notice">Simpan role, keaktifan, dan relasi akun ini? Password yang diisi akan mereset akses, mencabut sesi lama, dan mewajibkan ganti password saat login.</p>}
      {confirm && <button className="secondary" disabled={operation.busy} type="button" onClick={() => setConfirm(false)}>Koreksi isian</button>}
      <button disabled={operation.busy}>{confirm ? 'Konfirmasi simpan pengguna' : 'Tinjau perubahan pengguna'}</button>
    </form>
  </ConfirmDialog>
}
