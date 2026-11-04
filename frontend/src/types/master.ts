import type { Role } from './auth'
export interface ManagedUser {
  id: string; username: string; email: string; first_name: string; last_name: string
  role: Role; dealer: string | null; dealer_name?: string; is_active: boolean; must_change_password: boolean
}
export interface Assignment { id: string; agent: string; dealer: string; agent_username: string; dealer_name: string }
export interface AdminFee { key: string; value: string; updated_at?: string }
export interface UserFields { username: string; email: string; first_name: string; last_name: string; role: Role; dealer: string; password: string; is_active: boolean }
