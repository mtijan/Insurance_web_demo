export interface AppNotification {
  id: string
  event_type: string
  title: string
  message: string
  target_path: string
  assurance_id: string | null
  actor_role: string
  actor_username: string
  is_read: boolean
  read_at: string | null
  created_at: string
}

export interface NotificationFeed {
  unread_count: number
  items: AppNotification[]
}
