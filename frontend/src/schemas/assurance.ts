import { z } from 'zod'
import type { DraftFields, FieldErrors } from '../types/wizard'

const name = z.string().transform(value => value.trim().normalize('NFC')).refine(value => Array.from(value).length >= 3 && Array.from(value).length <= 100, 'Gunakan nama 3–100 karakter.').refine(value => /^[\p{L}\p{M} '.’\-‐]+$/u.test(value) && /\p{L}/u.test(value), 'Gunakan huruf, spasi, apostrof, titik, atau tanda hubung.')
const price = z.string().regex(/^\d{1,12}(\.\d{1,2})?$/, 'Gunakan nominal dengan maksimal dua desimal (titik).').refine(value => Number(value) >= 1000000, 'Harga pertanggungan minimal Rp1.000.000.')
const date = z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Isi tanggal yang sah.').refine(value => { const d = new Date(value + 'T00:00:00Z'); return !Number.isNaN(d.valueOf()) && d.toISOString().slice(0, 10) === value }, 'Isi tanggal kalender yang sah.')
export const draftSchema = z.object({
  dealer_id: z.uuid('Pilih dealer yang diizinkan.'), vehicle_category: z.enum(['MOTOR_BARU', 'MOTOR_LAMA']),
  policy_holder_name: name, policy_holder_nik: z.string().regex(/^[0-9]{16}$/, 'NIK harus tepat 16 digit angka.'),
  policy_holder_phone: z.string().max(20, 'Telepon maksimal 20 karakter.'), policy_holder_address: z.string(),
  vehicle_object: z.string().trim().min(1, 'Isi objek jaminan.').max(50, 'Maksimal 50 karakter.'),
  coverage_type: z.enum(['TLO', 'TLO_PLUS', 'KOMPRE_PLUS']), sum_insured: price,
  tenor_years: z.string().regex(/^[1-5]$/, 'Tenor harus 1–5 tahun.'), period_start: date,
  issuance_year: z.string().regex(/^[1-9][0-9]{3}$/, 'Tahun harus 1000–9999.'),
})
export const stepFields: (keyof DraftFields)[][] = [
  ['dealer_id', 'vehicle_category'], ['policy_holder_name', 'policy_holder_nik', 'policy_holder_phone', 'policy_holder_address'],
  ['vehicle_object', 'coverage_type', 'sum_insured', 'tenor_years', 'period_start', 'issuance_year'],
]
export function validateFields(values: DraftFields, keys: (keyof DraftFields)[] = Object.keys(values) as (keyof DraftFields)[]) {
  const result = draftSchema.safeParse(values)
  const errors: FieldErrors = {}
  if (!result.success) for (const issue of result.error.issues) {
    const key = issue.path[0] as keyof DraftFields
    if (keys.includes(key) && !errors[key]) errors[key] = issue.message
  }
  return errors
}
