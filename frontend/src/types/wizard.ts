export interface DraftFields {
  dealer_id: string
  vehicle_category: 'MOTOR_BARU' | 'MOTOR_LAMA'
  policy_holder_name: string
  policy_holder_nik: string
  policy_holder_phone: string
  policy_holder_address: string
  vehicle_object: string
  coverage_type: 'TLO' | 'TLO_PLUS' | 'KOMPRE_PLUS'
  sum_insured: string
  tenor_years: string
  period_start: string
  issuance_year: string
}
export type FieldErrors = Partial<Record<keyof DraftFields, string>>
export interface StepProps { values: DraftFields; errors: FieldErrors; change: (key: keyof DraftFields, value: string) => void; validate: (key: keyof DraftFields) => void }
export interface Premium { base_premium: string; admin_fee: string; total_premium: string }
