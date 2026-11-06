import { createPortal } from 'react-dom'
import { Link } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'
import { useIconTooltip } from '../../hooks/useIconTooltip'

type Props = { label: string; icon: LucideIcon; danger?: boolean } & (
  { to: string; onClick?: never; disabled?: never } | { to?: never; onClick: () => void; disabled?: boolean }
)
export function IconAction({ label, icon: Icon, danger = false, to, onClick, disabled }: Props) {
  const { anchor, popup, id, position, show, hide, leaveAnchor, leavePopup } = useIconTooltip()
  const className = `icon-action ${to ? 'action-link' : 'secondary'}${danger ? ' danger-outline' : ''}`
  const name = { 'aria-label': label, 'aria-labelledby': position ? id : undefined, className }
  return <span ref={anchor} className="icon-action-wrap" onFocus={show} onBlur={hide} onMouseEnter={show} onMouseLeave={leaveAnchor} onKeyDown={event => { if (event.key === 'Escape') hide() }}>
    {to ? <Link {...name} to={to} onClick={hide}><Icon size={20} aria-hidden="true" focusable="false" /></Link>
      : <button {...name} type="button" disabled={disabled} onClick={() => { hide(); onClick?.() }}><Icon size={20} aria-hidden="true" focusable="false" /></button>}
    {position && createPortal(<span ref={popup} id={id} role="tooltip" className={`icon-action-tooltip${position.above ? ' above' : ''}`} style={{ left: position.x, top: position.y }} onMouseLeave={leavePopup}>{label}</span>, document.body)}
  </span>
}
