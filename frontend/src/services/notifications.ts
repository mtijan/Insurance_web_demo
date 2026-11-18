import { api } from './apiClient'
import type { Envelope } from '../types/auth'
import type { AppNotification, NotificationFeed } from '../types/notification'

export const NOTIFICATIONS_CHANGED_EVENT = 'kevin:notifications-changed'

export function notifyNotificationsChanged() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(NOTIFICATIONS_CHANGED_EVENT))
  }
}

export async function fetchNotifications(limit = 20, signal?: AbortSignal) {
  const response = await api.get<Envelope<NotificationFeed>>('notifications/', {
    params: { limit },
    signal,
  })
  return response.data.data
}

export async function markNotificationRead(id: string) {
  const response = await api.post<Envelope<{ item: AppNotification; unread_count: number }>>(
    `notifications/${id}/read/`,
  )
  return response.data.data
}

export async function markAllNotificationsRead() {
  const response = await api.post<Envelope<{ marked_count: number; unread_count: number }>>(
    'notifications/read-all/',
  )
  return response.data.data
}
