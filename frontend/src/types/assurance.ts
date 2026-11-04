export interface AssuranceRow {
  id: string
  policy_holder_name: string
  dealer_name: string
  assurance_number: string | null
  status: string
  dealer_code: string
  vehicle_category: string
  coverage_type: string
  sum_insured: string
  total_premium: string
  created_at: string
  verification_stage: string
  data_verified: boolean
  documents_verified: boolean
}
export interface Document { id: string; document_type: string; view_url: string; file_size: number; original_filename: string }
export interface AssuranceDetail {
  id: string
  status: string
  can_edit: boolean
  policy_holder: { full_name: string; nik: string; phone: string; address: string }
  dealer: Dealer
  documents: Document[]
  required_documents: string[]
  missing_documents: string[]
  is_documents_complete: boolean
  assurance_number: string | null
  vehicle_category: 'MOTOR_BARU' | 'MOTOR_LAMA'
  vehicle_object: string
  coverage_type: 'TLO' | 'TLO_PLUS' | 'KOMPRE_PLUS'
  sum_insured: string
  tenor_years: number
  base_premium: string
  admin_fee: string
  total_premium: string
  period_start: string
  period_end: string
  issuance_year: number
  review_notes: string
  verification_stage: string
  data_verified: boolean
  documents_verified: boolean
  review_history: ReviewEvent[]
  updated_at: string
}
export interface ReviewEvent { id: string; action: string; section: string; review_notes: string; actor_role: string; created_at: string }
import type { Dealer } from './dealer'
