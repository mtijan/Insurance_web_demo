import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'
import { SidebarNav } from './SidebarNav'

export function MobileDrawer({ open, close }: { open: boolean; close: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const node = dialog.current
    if (!node || !open) return
    const previous = document.activeElement as HTMLElement | null
    node.showModal()
    document.body.style.overflow = 'hidden'
    const media = matchMedia('(min-width: 1024px)')
    const resize = () => { if (media.matches) close() }
    media.addEventListener('change', resize)
    return () => { node.close(); document.body.style.overflow = ''; media.removeEventListener('change', resize); previous?.focus() }
  }, [open, close])
  return <dialog ref={dialog} className="mobile-drawer" aria-label="Menu utama" onCancel={close} onKeyDown={event => {
    if (event.key !== 'Tab') return
    const items = dialog.current?.querySelectorAll<HTMLElement>('button:not(:disabled), a[href]')
    if (!items?.length) return
    const first = items[0], last = items[items.length - 1]
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
    if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
  }}>
    <button className="drawer-close" autoFocus onClick={close}><X size={20} aria-hidden="true" />Tutup menu</button>
    <SidebarNav onNavigate={close} />
  </dialog>
}
