import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { AppLayout } from './components/layout/AppLayout'
import { LoginPage } from './pages/LoginPage'
import { AssurancesPage } from './pages/AssurancesPage'
import { AssuranceDetailPage } from './pages/AssuranceDetailPage'
import { AuditPage } from './pages/AuditPage'

export default function App() {
  return <BrowserRouter><AuthProvider>
    <a className="skip-link" href="#main">Lewati ke konten utama</a>
    <header className="brand">Kevin Assurance <span>Pengelolaan jaminan kendaraan</span></header>
    <main id="main" tabIndex={-1}>
      <Routes>
        <Route path="/login" element={<LoginPage key="login" />} />
        <Route path="/change-password" element={<LoginPage key="password" change />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route index element={<AssurancesPage />} />
            <Route path="/assurances/:id" element={<AssuranceDetailPage />} />
            <Route element={<ProtectedRoute roles={['SUPER_ADMIN']} />}>
              <Route path="/audit" element={<AuditPage />} />
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </main>
  </AuthProvider></BrowserRouter>
}
