import { useState } from 'react'
import { useResource } from '../../hooks/useResource'
import type { Dealer } from '../../types/dealer'
import type { StepProps } from '../../types/wizard'
import { Feedback } from '../shared/Feedback'

export function StepDealer({ values, errors, change }: StepProps) {
  const dealers = useResource<Dealer[]>('dealers/?active_only=true&summary=true')
  const [search, setSearch] = useState('')
  return <section className="panel"><h2>Dealer & kategori</h2>
    <Feedback {...dealers} retry={dealers.reload} />
    {dealers.data && !dealers.data.length && <p className="notice">Tidak ada dealer aktif dalam lingkup akun. Hubungi Super Admin untuk memeriksa penugasan.</p>}
    <div className="form-grid"><div className="field"><label htmlFor="dealer-search">Cari dealer</label><input id="dealer-search" type="search" placeholder="Cari nama atau kode…" value={search} onChange={e => setSearch(e.target.value)} /><label htmlFor="dealer_id" id="dealer-label">Asal dealer</label><select id="dealer_id" aria-labelledby="dealer-label" value={values.dealer_id} aria-invalid={!!errors.dealer_id} aria-describedby={errors.dealer_id ? 'dealer-error' : undefined} onChange={e => change('dealer_id', e.target.value)}><option value="">Pilih dealer</option>{dealers.data?.filter(d => d.id === values.dealer_id || `${d.code} ${d.name}`.toLocaleLowerCase().includes(search.toLocaleLowerCase())).map(d => <option key={d.id} value={d.id}>{d.code} · {d.name}</option>)}</select>{errors.dealer_id && <small id="dealer-error" className="field-error">{errors.dealer_id}</small>}</div>
    <label><span id="category-label">Kategori motor</span><select id="vehicle_category" aria-labelledby="category-label" value={values.vehicle_category} onChange={e => change('vehicle_category', e.target.value)}><option value="MOTOR_BARU">Motor Baru</option><option value="MOTOR_LAMA">Motor Lama</option></select></label></div>
    <p className="muted">Pilihan mengikuti dealer aktif yang diizinkan server. Perubahan tersimpan hanya setelah Simpan draft berhasil.</p>
  </section>
}
