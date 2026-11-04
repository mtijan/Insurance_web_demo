import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../../auth/authState'
import { navigation } from './navigation'
import { LogoutButton } from './LogoutButton'

export function SidebarNav({ collapsed = false, onNavigate }: { collapsed?: boolean; onNavigate?: () => void }) {
  const { user } = useAuth()
  const { pathname } = useLocation()
  const [dismissed, setDismissed] = useState('')
  const items = navigation.filter(item => user && item.roles.includes(user.role))
  return <>
    <div className="sidebar-brand" aria-label="Kevin Assurance"><span aria-hidden="true">KA</span>{!collapsed && <strong>Kevin Assurance<small>Jaminan kendaraan</small></strong>}</div>
    <nav aria-label="Navigasi utama">
      {['Operasional', 'Master data', 'Administrasi'].filter(group => items.some(item => item.group === group)).map(group => <section key={group} aria-label={group}>
        <h2 className={collapsed ? 'sr-only' : 'nav-group'}>{group}</h2>
        {items.filter(item => item.group === group).map(item => <div className="nav-item" key={item.to} onKeyDown={event => { if (event.key === 'Escape') setDismissed(item.to) }} onBlur={() => setDismissed('')} onMouseLeave={() => setDismissed('')}>
          {item.ready ? <Link to={item.to} onClick={onNavigate} aria-label={collapsed ? item.label : undefined}
            aria-current={activeRoute(item.to, pathname) ? 'page' : undefined} className={activeRoute(item.to, pathname) ? 'active' : undefined}>
            <item.icon size={20} aria-hidden="true" />{!collapsed && <span>{item.label}</span>}
          </Link> : <span className="nav-unavailable" aria-label={`${item.label}: belum tersedia`}><item.icon size={20} aria-hidden="true" />{!collapsed && <span>{item.label}<small>Belum tersedia</small></span>}</span>}
          {collapsed && <span className="nav-tooltip" role="tooltip" hidden={dismissed === item.to}>{item.label}{!item.ready && ' · Belum tersedia'}</span>}
        </div>)}
      </section>)}
    </nav>
    <footer className="sidebar-footer">{!collapsed && <p>{user?.username}<small>{user?.role.replaceAll('_', ' ')}</small></p>}<LogoutButton compact={collapsed} /></footer>
  </>
}
function activeRoute(target: string, path: string) {
  if (target === '/') return path === '/' || (path.startsWith('/assurances/') && path !== '/assurances/new')
  return path === target || path.startsWith(target + '/')
}
