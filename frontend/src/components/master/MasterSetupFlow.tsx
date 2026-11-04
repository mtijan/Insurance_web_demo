import { Link } from 'react-router-dom'

export function MasterSetupFlow({ current }: { current: 'dealer' | 'user' | 'assignment' }) {
  const steps = [{ key: 'dealer', to: '/dealers', label: '1. Siapkan dealer' }, { key: 'user', to: '/admin/users', label: '2. Buat akun pengguna' }, { key: 'assignment', to: '/admin/assignments', label: '3. Tugaskan Agent' }]
  return <nav className="panel setup-flow" aria-label="Langkah pengelolaan"><ol>{steps.map(step => <li key={step.key}><Link to={step.to} aria-current={current === step.key ? 'step' : undefined}>{step.label}</Link></li>)}</ol>
    <p className="muted">Akun Dealer terikat pada satu dealer. Akun Agent mendapat dealer binaan melalui penugasan, sesudah akunnya dibuat.</p>
  </nav>
}
