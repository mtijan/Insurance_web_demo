import { useState } from 'react'
import { useResource } from '../../hooks/useResource'
import type { Dealer } from '../../types/dealer'
import type { StepProps } from '../../types/wizard'
import { Feedback } from '../shared/Feedback'

export function StepDealer({ dealer, ...fields }: StepProps & { dealer?: Dealer }) {
  return <section className="panel"><h2>{dealer ? 'Kategori motor' : 'Dealer & kategori'}</h2>
    {dealer && <p className="muted">Pengajuan dari {dealer.code} · {dealer.name}. Dealer mengikuti akun Anda secara otomatis.</p>}
    <div className="form-grid">
      {!dealer && <DealerSelection {...fields} />}
      <div className="field"><label htmlFor="vehicle_category" id="category-label">Kategori motor</label><select id="vehicle_category" aria-labelledby="category-label" value={fields.values.vehicle_category} onChange={e => fields.change('vehicle_category', e.target.value)}><option value="MOTOR_BARU">Motor Baru</option><option value="MOTOR_LAMA">Motor Lama</option></select></div>
    </div>
    <p className="muted">Perubahan tersimpan setelah Simpan draft berhasil.</p>
  </section>
}
function DealerSelection({ values, errors, change }: StepProps) {
  const dealers = useResource<Dealer[]>('dealers/?active_only=true&summary=true')
  const [search, setSearch] = useState('')
  return <>
    <Feedback {...dealers} retry={dealers.reload} />
    {dealers.data && !dealers.data.length && <p className="notice">Tidak ada dealer aktif dalam lingkup akun. Hubungi Super Admin untuk memeriksa penugasan.</p>}
      <div className="field"><label htmlFor="dealer-search">Cari dealer</label><input id="dealer-search" type="search" placeholder="Cari nama atau kode…" value={search} onChange={e => setSearch(e.target.value)} /></div>
      <div className="field"><label htmlFor="dealer_id" id="dealer-label">Asal dealer</label><select id="dealer_id" aria-labelledby="dealer-label" value={values.dealer_id} aria-invalid={!!errors.dealer_id} aria-describedby={errors.dealer_id ? 'dealer-error' : undefined} onChange={e => change('dealer_id', e.target.value)}><option value="">Pilih dealer</option>{dealers.data?.filter(d => d.id === values.dealer_id || `${d.code} ${d.name}`.toLocaleLowerCase().includes(search.toLocaleLowerCase())).map(d => <option key={d.id} value={d.id}>{d.code} · {d.name}</option>)}</select>{errors.dealer_id && <small id="dealer-error" className="field-error">{errors.dealer_id}</small>}</div>
  </>
}
