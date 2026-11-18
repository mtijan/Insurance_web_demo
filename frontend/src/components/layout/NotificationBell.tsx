import { useEffect, useId, useRef, useState } from 'react'
import type { RefObject } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell, CheckCheck, RefreshCw } from 'lucide-react'
import { useNotifications } from '../../hooks/useNotifications'
import type { AppNotification } from '../../types/notification'
import type { User } from '../../types/auth'
import { isSafeInternalPath } from '../../utils/roleLabels'
import { NotificationItem } from './NotificationItem'

function usePopoverDismiss(
  open: boolean,
  setOpen: (value: boolean) => void,
  wrapRef: RefObject<HTMLDivElement | null>,
  triggerRef: RefObject<HTMLButtonElement | null>,
) {
  useEffect(() => {
    if (!open) return
    const onPointer = (event: MouseEvent) => { if (!wrapRef.current?.contains(event.target as Node)) setOpen(false) }
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') { setOpen(false); triggerRef.current?.focus() } }
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => { document.removeEventListener('mousedown', onPointer); document.removeEventListener('keydown', onKey) }
  }, [open, setOpen, triggerRef, wrapRef])
}

function NotificationPopoverBody({
  state,
  onSelect,
}: {
  state: ReturnType<typeof useNotifications>
  onSelect: (item: AppNotification) => void
}) {
  if (state.loading && state.items.length === 0) return <p role="status" className="notif-state">Memuat notifikasi…</p>
  if (state.error) {
    return (
      <div role="alert" className="notif-state">
        <p>{state.error}</p>
        <button type="button" className="secondary notif-retry-btn" onClick={() => void state.reload()}>
          <RefreshCw size={14} aria-hidden="true" />Muat ulang
        </button>
      </div>
    )
  }
  if (!state.items.length) return <p className="notif-state">Belum ada notifikasi.</p>
  return <ol className="notif-list">{state.items.map(item => <NotificationItem key={item.id} item={item} onSelect={onSelect} />)}</ol>
}

export function NotificationBell({ user }: { user: User }) {
  const [open, setOpen] = useState(false)
  const panelId = useId()
  const wrapRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const navigate = useNavigate()
  const state = useNotifications(!user.must_change_password)
  usePopoverDismiss(open, setOpen, wrapRef, triggerRef)

  async function handleSelect(item: AppNotification) {
    if (!item.is_read) await state.markRead(item.id)
    setOpen(false)
    if (isSafeInternalPath(item.target_path)) navigate(item.target_path)
  }

  const badgeText = state.unreadCount > 99 ? '99+' : String(state.unreadCount)
  const bellLabel = state.unreadCount > 0 ? `Notifikasi, ${state.unreadCount} belum dibaca` : 'Notifikasi'
  return (
    <div ref={wrapRef} className="notif-wrap">
      <button ref={triggerRef} type="button" className="secondary notif-bell-btn" aria-expanded={open} aria-controls={panelId} aria-label={bellLabel} onClick={() => { const next = !open; setOpen(next); if (next) void state.reload() }}>
        <Bell size={18} aria-hidden="true" />
        {state.unreadCount > 0 && <span className="notif-count" aria-hidden="true">{badgeText}</span>}
      </button>
      {open && (
        <section id={panelId} className="notif-popover" aria-label="Notifikasi aplikasi">
          <div className="notif-popover-head">
            <h2>Notifikasi</h2>
            <button type="button" className="secondary notif-mark-all-btn" disabled={state.busy || state.unreadCount === 0} onClick={() => void state.markAllRead()}>
              <CheckCheck size={14} aria-hidden="true" />Tandai semua dibaca
            </button>
          </div>
          <NotificationPopoverBody state={state} onSelect={item => void handleSelect(item)} />
        </section>
      )}
    </div>
  )
}
