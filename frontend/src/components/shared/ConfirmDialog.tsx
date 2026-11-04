import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'

export function ConfirmDialog({ title, children, close, busy = false }: { title: string; children: ReactNode; close: () => void; busy?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const node = ref.current!, previous = document.activeElement as HTMLElement | null
    node.showModal(); document.body.style.overflow = 'hidden'
    return () => { node.close(); document.body.style.overflow = ''; if (previous?.isConnected) previous.focus() }
  }, [])
  return <dialog className="confirm-dialog" ref={ref} aria-labelledby="dialog-title" onCancel={event => { event.preventDefault(); if (!busy) close() }} onKeyDown={event => {
    if (event.key !== 'Tab') return
    const items = ref.current?.querySelectorAll<HTMLElement>('button:not(:disabled), input, textarea, select, a[href]')
    if (!items?.length) { event.preventDefault(); return }
    const first = items[0], last = items[items.length - 1]
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
    if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
  }}><h2 id="dialog-title">{title}</h2><button className="secondary" autoFocus disabled={busy} onClick={close}>Batal</button>{children}</dialog>
}
