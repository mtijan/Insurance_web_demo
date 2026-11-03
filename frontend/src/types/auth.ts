export type Role = 'SUPER_ADMIN' | 'ADMIN' | 'AGENT' | 'DEALER'
export interface User {
  id: string
  username: string
  role: Role
  must_change_password: boolean
}
export interface Envelope<T> { success: boolean; data: T }
