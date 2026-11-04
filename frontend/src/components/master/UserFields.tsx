import type { UserFields as Values } from '../../types/master'
import type { Dealer } from '../../types/dealer'
import type { Role } from '../../types/auth'
import { Field } from '../shared/Field'

export function UserFields({ values, change, dealers }: { values: Values; change: (key: keyof Values, value: string | boolean) => void; dealers: Dealer[] }) {
  return <div className="form-grid">
    <Field name="username" label="Username" autoComplete="off" spellCheck={false} value={values.username} maxLength={150} onChange={e => change('username', e.target.value)} />
    <Field name="email" label="Email" type="email" autoComplete="off" spellCheck={false} value={values.email} onChange={e => change('email', e.target.value)} />
    <Field name="first_name" label="Nama depan" value={values.first_name} onChange={e => change('first_name', e.target.value)} />
    <Field name="last_name" label="Nama belakang" value={values.last_name} onChange={e => change('last_name', e.target.value)} />
    <label><span id="role-label">Role pengguna</span><select aria-labelledby="role-label" value={values.role} onChange={e => change('role', e.target.value as Role)}>{['SUPER_ADMIN', 'ADMIN', 'AGENT', 'DEALER'].map(role => <option key={role}>{role}</option>)}</select></label>
    {values.role === 'DEALER' && <label><span id="user-dealer-label">Dealer pengguna</span><select aria-labelledby="user-dealer-label" value={values.dealer} onChange={e => change('dealer', e.target.value)}><option value="">Pilih dealer untuk akun ini</option>{dealers.map(d => <option key={d.id} value={d.id}>{d.name}{!d.is_active && ' (nonaktif)'}</option>)}</select></label>}
    {values.role === 'AGENT' && <p className="notice">Dealer binaan ditentukan pada langkah Penugasan agent setelah akun disimpan. Satu Agent dapat mendampingi beberapa dealer.</p>}
    <Field name="password" label="Password provisioning/reset" type="password" autoComplete="new-password" value={values.password} onChange={e => change('password', e.target.value)} hint="Kosong: password existing tetap; akun baru tidak dapat login sampai diberikan password. Password baru memaksa ganti saat login." />
    <label className="check-field"><input type="checkbox" checked={values.is_active} onChange={e => change('is_active', e.target.checked)} />Akun aktif</label>
  </div>
}
