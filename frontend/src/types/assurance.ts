export interface AssuranceRow {
  id: string
  policy_holder_name: string
  dealer_name: string
  assurance_number: string | null
  status: string
}
export interface Document { id: string; document_type: string; view_url: string }
export interface AssuranceDetail {
  id: string
  status: string
  can_edit: boolean
  policy_holder: { full_name: string }
  dealer: Dealer
  documents: Document[]
  required_documents: string[]
}
import type { Dealer } from './dealer'
