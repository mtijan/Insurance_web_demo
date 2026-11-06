import type { StepProps } from '../../types/wizard'
import { Field } from '../shared/Field'
import { usePremiumCalculator } from '../../hooks/usePremiumCalculator'
import { PremiumSummaryCard } from '../pricing/PremiumSummaryCard'
import { Feedback } from '../shared/Feedback'

export function StepVehicleDetails(props: StepProps) {
  const { values, errors, change, validate } = props
  const premium = usePremiumCalculator(values)
  return <section className="panel"><h2>Jaminan & premi</h2><div className="form-grid">
    <Field name="vehicle_object" label="Objek jaminan" value={values.vehicle_object} error={errors.vehicle_object} onChange={e => change('vehicle_object', e.target.value)} onBlur={() => validate('vehicle_object')} />
    <Field name="sum_insured" label="Harga pertanggungan (Rp)" inputMode="decimal" value={values.sum_insured} error={errors.sum_insured} hint="Minimal Rp1.000.000; gunakan titik untuk desimal." onChange={e => change('sum_insured', e.target.value)} onBlur={() => validate('sum_insured')} />
    <label><span id="coverage-label">Jenis jaminan</span><select id="coverage_type" aria-labelledby="coverage-label" value={values.coverage_type} onChange={e => change('coverage_type', e.target.value)}><option value="TLO">TLO</option><option value="TLO_PLUS">TLO+</option><option value="KOMPRE_PLUS">Kompre+</option></select></label>
    <label><span id="tenor-label">Tenor (tahun)</span><select id="tenor_years" aria-labelledby="tenor-label" value={values.tenor_years} onChange={e => change('tenor_years', e.target.value)}>{[1, 2, 3, 4, 5].map(n => <option key={n}>{n}</option>)}</select></label>
    <Field name="period_start" label="Tanggal mulai" type="date" value={values.period_start} error={errors.period_start} onChange={e => change('period_start', e.target.value)} />
    <Field name="issuance_year" label="Tahun terbit jaminan" inputMode="numeric" value={values.issuance_year} error={errors.issuance_year} onChange={e => change('issuance_year', e.target.value)} />
  </div>{premium.valid && <Feedback {...premium} retry={premium.reload} />}{premium.data && <PremiumSummaryCard premium={premium.data} tenorYears={Number(values.tenor_years)} />}<p className="muted">Tanggal akhir dihitung otomatis saat draft disimpan. Simpan draft untuk melanjutkan ke Dokumen.</p></section>
}
