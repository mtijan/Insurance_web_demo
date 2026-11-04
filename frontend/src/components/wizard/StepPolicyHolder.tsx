import type { StepProps } from '../../types/wizard'
import { Field } from '../shared/Field'

export function StepPolicyHolder({ values, errors, change, validate }: StepProps) {
  return <section className="panel"><h2>Tertanggung</h2><div className="form-grid">
    <Field name="policy_holder_name" label="Nama tertanggung" autoComplete="off" value={values.policy_holder_name} error={errors.policy_holder_name} hint="3–100 karakter; huruf Unicode, spasi, apostrof, titik, tanda hubung." onChange={e => change('policy_holder_name', e.target.value)} onBlur={() => validate('policy_holder_name')} />
    <Field name="policy_holder_nik" label="NIK" inputMode="numeric" autoComplete="off" value={values.policy_holder_nik} error={errors.policy_holder_nik} hint="Tepat 16 digit; nol di depan dipertahankan. Validasi format saja." onChange={e => change('policy_holder_nik', e.target.value)} onBlur={() => validate('policy_holder_nik')} />
    <Field name="policy_holder_phone" label="Telepon (opsional)" type="tel" autoComplete="off" maxLength={20} value={values.policy_holder_phone} error={errors.policy_holder_phone} onChange={e => change('policy_holder_phone', e.target.value)} />
    <label>Alamat (opsional)<textarea name="policy_holder_address" autoComplete="off" value={values.policy_holder_address} onChange={e => change('policy_holder_address', e.target.value)} /></label>
  </div><p className="muted">Isian berada di memori halaman sampai Simpan draft berhasil. Tidak ada autosave.</p></section>
}
