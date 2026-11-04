import { Suspense, useCallback, useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Menu, PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { SidebarNav } from './SidebarNav'
import { MobileDrawer } from './MobileDrawer'
import { NavigationSafety } from './navigationSafety'
import type { SafetyState } from './navigationSafety'

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const [drawerKey, setDrawerKey] = useState<string | null>(null)
  const open = drawerKey === location.key
  const [safety, setSafety] = useState<SafetyState>({ dirty: false, busy: false })
  const close = useCallback(() => setDrawerKey(null), [])
  useEffect(() => {
    const task = requestAnimationFrame(() => {
      document.querySelector<HTMLElement>('h1')?.setAttribute('tabindex', '-1')
      document.querySelector<HTMLElement>('h1')?.focus()
      window.scrollTo(0, 0)
    })
    return () => cancelAnimationFrame(task)
  }, [location.pathname, location.key])
  return <NavigationSafety.Provider value={{ safety, setSafety }}><div className={`app-shell ${collapsed ? 'collapsed' : ''}`}>
    <aside className="desktop-sidebar"><SidebarNav collapsed={collapsed} /></aside>
    <div className="app-workspace">
      <header className="context-header">
        <button className="secondary mobile-trigger" aria-expanded={open} aria-label="Buka menu" onClick={() => setDrawerKey(location.key)}><Menu size={20} aria-hidden="true" /><span>Menu</span></button>
        <button className="secondary desktop-trigger" aria-expanded={!collapsed} aria-label={collapsed ? 'Perluas sidebar' : 'Ciutkan sidebar'} onClick={() => setCollapsed(value => !value)}>{collapsed ? <PanelLeftOpen aria-hidden="true" /> : <PanelLeftClose aria-hidden="true" />}</button>
        <span>Kevin Assurance <small>Pengelolaan jaminan kendaraan</small></span>
      </header>
      <main id="main" tabIndex={-1}><Suspense fallback={<p role="status">Memuat halaman…</p>}><Outlet /></Suspense></main>
    </div>
    <MobileDrawer open={open} close={close} />
  </div></NavigationSafety.Provider>
}
