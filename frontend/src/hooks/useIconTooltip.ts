import { useCallback, useEffect, useId, useRef, useState } from 'react'
import type { MouseEvent } from 'react'

export function useIconTooltip() {
  const anchor = useRef<HTMLSpanElement>(null), popup = useRef<HTMLSpanElement>(null)
  const [position, setPosition] = useState<{ x: number; y: number; above: boolean } | null>(null)
  const id = useId(), open = position !== null
  const hide = useCallback(() => setPosition(null), [])
  useEffect(() => {
    if (!open) return
    window.addEventListener('scroll', hide, true); window.addEventListener('resize', hide)
    return () => { window.removeEventListener('scroll', hide, true); window.removeEventListener('resize', hide) }
  }, [open, hide])
  function show() {
    if (!anchor.current) return
    const rect = anchor.current.getBoundingClientRect(), half = Math.min(280, window.innerWidth - 16) / 2
    const x = Math.max(half + 8, Math.min(window.innerWidth - half - 8, rect.left + rect.width / 2))
    const above = rect.top >= 140
    setPosition({ x, y: above ? rect.top : rect.bottom, above })
  }
  function leaveAnchor(event: MouseEvent<HTMLElement>) {
    if (!(event.relatedTarget instanceof Node) || !popup.current?.contains(event.relatedTarget)) hide()
  }
  function leavePopup(event: MouseEvent<HTMLElement>) {
    if (!(event.relatedTarget instanceof Node) || !anchor.current?.contains(event.relatedTarget)) hide()
  }
  return { anchor, popup, id, position, show, hide, leaveAnchor, leavePopup }
}
