import { useCallback, useEffect, useState } from 'react'
import { errorMessage } from '../services/apiClient'
import {
  fetchNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  NOTIFICATIONS_CHANGED_EVENT,
} from '../services/notifications'
import type { AppNotification } from '../types/notification'

const POLL_INTERVAL_MS = 30000

function useNotificationListeners(enabled: boolean, reload: (signal?: AbortSignal) => Promise<void>) {
  useEffect(() => {
    if (!enabled) return
    const controller = new AbortController()
    queueMicrotask(() => { if (!controller.signal.aborted) void reload(controller.signal) })
    const onRefresh = () => { void reload() }
    const onFocus = () => { if (document.visibilityState === 'visible') void reload() }
    const timer = window.setInterval(onFocus, POLL_INTERVAL_MS)
    window.addEventListener(NOTIFICATIONS_CHANGED_EVENT, onRefresh)
    window.addEventListener('focus', onFocus)
    document.addEventListener('visibilitychange', onFocus)
    return () => {
      controller.abort(); window.clearInterval(timer)
      window.removeEventListener(NOTIFICATIONS_CHANGED_EVENT, onRefresh)
      window.removeEventListener('focus', onFocus)
      document.removeEventListener('visibilitychange', onFocus)
    }
  }, [enabled, reload])
}

function useNotificationFeed(enabled: boolean) {
  const [items, setItems] = useState<AppNotification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const reload = useCallback(async (signal?: AbortSignal) => {
    if (!enabled) return
    try {
      const feed = await fetchNotifications(20, signal)
      if (!signal?.aborted) { setItems(feed.items); setUnreadCount(feed.unread_count); setError('') }
    } catch (failure) {
      if (!signal?.aborted) setError(errorMessage(failure))
    } finally {
      if (!signal?.aborted) setLoading(false)
    }
  }, [enabled])
  useNotificationListeners(enabled, reload)
  return { items, setItems, unreadCount, setUnreadCount, loading, error, setError, reload }
}

export function useNotifications(enabled: boolean) {
  const feed = useNotificationFeed(enabled)
  const [busy, setBusy] = useState(false)
  const { setItems, setUnreadCount, setError } = feed

  const markRead = useCallback(async (id: string) => {
    try {
      const result = await markNotificationRead(id)
      setUnreadCount(result.unread_count)
      setItems(current => current.map(item => (item.id === id ? result.item : item)))
    } catch (failure) { setError(errorMessage(failure)) }
  }, [setError, setItems, setUnreadCount])

  const markAllRead = useCallback(async () => {
    setBusy(true)
    try {
      const result = await markAllNotificationsRead()
      setUnreadCount(result.unread_count)
      const stamp = new Date().toISOString()
      setItems(current => current.map(item => ({ ...item, is_read: true, read_at: item.read_at ?? stamp })))
      setError('')
    } catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }, [setError, setItems, setUnreadCount])

  return { items: feed.items, unreadCount: feed.unreadCount, loading: feed.loading, busy, error: feed.error, reload: feed.reload, markRead, markAllRead }
}
