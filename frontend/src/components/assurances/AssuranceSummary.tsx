import type { AssuranceDetail } from '../../types/assurance'
import { money, dateLabel } from '../../utils/format'

export function AssuranceSummary({ detail: d }: { detail: AssuranceDetail }) {
  return <section className="panel" aria-label="Data jaminan">
    <h2>Data pengajuan dan premi</h2>
    <dl className="data-grid">
      <div><dt>NIK</dt><dd>{d.policy_holder.nik}</dd></div><div><dt>Dealer</dt><dd>{d.dealer.name}</dd></div>
      <div><dt>Telepon</dt><dd>{d.policy_holder.phone || 'Tidak diisi'}</dd></div><div><dt>Alamat</dt><dd>{d.policy_holder.address || 'Tidak diisi'}</dd></div>
      <div><dt>Kategori</dt><dd>{d.vehicle_category === 'MOTOR_BARU' ? 'Motor Baru' : 'Motor Lama'}</dd></div><div><dt>Jaminan</dt><dd>{d.coverage_type.replaceAll('_PLUS', '+')} · {d.tenor_years} tahun</dd></div>
      <div><dt>Harga pertanggungan</dt><dd>{money(d.sum_insured)}</dd></div><div><dt>Periode</dt><dd>{dateLabel(d.period_start)} – {dateLabel(d.period_end)}</dd></div>
      <div><dt>Premi murni</dt><dd>{money(d.base_premium)}</dd></div><div><dt>Biaya admin (snapshot)</dt><dd>{money(d.admin_fee)}</dd></div>
      <div><dt>Total premi</dt><dd><strong>{money(d.total_premium)}</strong></dd></div><div><dt>Nomor jaminan</dt><dd>{d.assurance_number ?? 'Belum diterbitkan'}</dd></div>
    </dl>
  </section>
}
