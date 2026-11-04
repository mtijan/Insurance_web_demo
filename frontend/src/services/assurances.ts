import { api } from './apiClient'
import { draftSchema } from '../schemas/assurance'
import type { AssuranceDetail } from '../types/assurance'
import type { Envelope } from '../types/auth'
import type { DraftFields } from '../types/wizard'

export async function saveDraft(values: DraftFields, id?: string) {
  const valid = draftSchema.parse(values)
  const payload = { ...valid, tenor_years: Number(valid.tenor_years), issuance_year: Number(valid.issuance_year) }
  const response = id ? await api.patch<Envelope<AssuranceDetail>>(`assurances/${id}/`, payload) : await api.post<Envelope<AssuranceDetail>>('assurances/', payload)
  return response.data.data
}
export async function getAssurance(id: string) { return (await api.get<Envelope<AssuranceDetail>>(`assurances/${id}/`)).data.data }
export function draftValues(detail?: AssuranceDetail): DraftFields {
  if (detail) return { dealer_id: detail.dealer.id, vehicle_category: detail.vehicle_category, policy_holder_name: detail.policy_holder.full_name,
    policy_holder_nik: detail.policy_holder.nik, policy_holder_phone: detail.policy_holder.phone ?? '', policy_holder_address: detail.policy_holder.address ?? '',
    vehicle_object: detail.vehicle_object, coverage_type: detail.coverage_type, sum_insured: detail.sum_insured, tenor_years: String(detail.tenor_years), period_start: detail.period_start, issuance_year: String(detail.issuance_year) }
  const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Jakarta', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date())
  return { dealer_id: '', vehicle_category: 'MOTOR_BARU', policy_holder_name: '', policy_holder_nik: '', policy_holder_phone: '', policy_holder_address: '', vehicle_object: 'Sepeda Motor', coverage_type: 'TLO', sum_insured: '', tenor_years: '1', period_start: today, issuance_year: today.slice(0, 4) }
}
