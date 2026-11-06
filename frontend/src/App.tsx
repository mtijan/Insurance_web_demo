import { createBrowserRouter, createRoutesFromElements, Navigate, Outlet, Route, RouterProvider } from 'react-router-dom'
import { lazy } from 'react'
import { AuthProvider } from './auth/AuthContext'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { AppLayout } from './components/layout/AppLayout'
import { LoginPage } from './pages/LoginPage'
import { AssurancesPage } from './pages/AssurancesPage'
import { AssuranceDetailPage } from './pages/AssuranceDetailPage'
import { AuditPage } from './pages/AuditPage'
import { DashboardPage } from './pages/DashboardPage'
const AssuranceFormPage = lazy(async () => ({ default: (await import('./pages/AssuranceFormPage')).AssuranceFormPage }))
const DealerApplicationsPage = lazy(async () => ({ default: (await import('./pages/DealerApplicationsPage')).DealerApplicationsPage }))
const AdminReviewPage = lazy(async () => ({ default: (await import('./pages/AdminReviewPage')).AdminReviewPage }))
const DealersPage = lazy(async () => ({ default: (await import('./pages/DealersPage')).DealersPage }))
const UsersPage = lazy(async () => ({ default: (await import('./pages/admin/UsersPage')).UsersPage }))
const AssignmentsPage = lazy(async () => ({ default: (await import('./pages/admin/AssignmentsPage')).AssignmentsPage }))
const AdminFeePage = lazy(async () => ({ default: (await import('./pages/admin/AdminFeePage')).AdminFeePage }))
const ReportsPage = lazy(async () => ({ default: (await import('./pages/admin/ReportsPage')).ReportsPage }))

function Root() {
  return <AuthProvider>
    <a className="skip-link" href="#main">Lewati ke konten utama</a>
    <Outlet />
  </AuthProvider>
}
function AuthLayout() {
  return <><header className="brand">Kevin Assurance <span>Pengelolaan jaminan kendaraan</span></header><main id="main" tabIndex={-1}><Outlet /></main></>
}
const router = createBrowserRouter(createRoutesFromElements(
  <Route element={<Root />}>
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage key="login" />} />
        <Route path="/change-password" element={<LoginPage key="password" change />} />
      </Route>
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route index element={<AssurancesPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/dealers" element={<DealersPage />} />
            <Route path="/assurances/new" element={<AssuranceFormPage />} />
            <Route element={<ProtectedRoute roles={['DEALER']} />}>
              <Route path="/assurances/drafts" element={<DealerApplicationsPage key="drafts" drafts />} />
              <Route path="/assurances/progress" element={<DealerApplicationsPage key="progress" />} />
            </Route>
            <Route path="/assurances/:id/edit" element={<AssuranceFormPage />} />
            <Route path="/assurances/:id" element={<AssuranceDetailPage />} />
            <Route element={<ProtectedRoute roles={['AGENT']} />}>
              <Route path="/inspection" element={<AssurancesPage inspection />} />
            </Route>
            <Route element={<ProtectedRoute roles={['SUPER_ADMIN', 'ADMIN']} />}>
              <Route path="/review" element={<AssurancesPage review />} />
              <Route path="/review/:id" element={<AdminReviewPage />} />
            </Route>
            <Route element={<ProtectedRoute roles={['SUPER_ADMIN']} />}>
              <Route path="/audit" element={<AuditPage />} />
              <Route path="/admin/users" element={<UsersPage />} />
              <Route path="/admin/assignments" element={<AssignmentsPage />} />
              <Route path="/admin/settings/admin-fee" element={<AdminFeePage />} />
              <Route path="/admin/reports" element={<ReportsPage />} />
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
  </Route>,
))
export default function App() { return <RouterProvider router={router} /> }
