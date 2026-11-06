import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/authState'
import { useAuthForm } from '../auth/useAuthForm'

type AuthForm = ReturnType<typeof useAuthForm>
export function LoginPage({ change = false }: { change?: boolean }) {
  const { user, loading, error: sessionError } = useAuth()
  const location = useLocation()
  const form = useAuthForm(change)
  if (loading) return <p role="status">Memeriksa sesi…</p>
  if (change && !user) return <Navigate to={form.completed ? '/login?changed=1' : '/login'} replace />
  if (!change && user) return <Navigate to={user.must_change_password ? '/change-password' : user.role === 'DEALER' ? '/assurances/new' : '/'} replace />
  return <AuthCard change={change} form={form} sessionError={sessionError} changed={new URLSearchParams(location.search).has('changed')} />
}
function AuthCard({ change, form, sessionError, changed }: { change: boolean; form: AuthForm; sessionError: string; changed: boolean }) {
  const { error: formError, busy, errorRef, submit, exit } = form
  const error = formError || sessionError
  return <section className="auth-card" aria-labelledby="auth-title">
    <p className="eyebrow">Akses internal</p><AuthIntro change={change} />
    {changed && <p role="status">Password berhasil diganti. Silakan masuk kembali.</p>}
    {error && <p className="error" role="alert" tabIndex={-1} ref={errorRef}>{error}</p>}
    <form onSubmit={submit} aria-busy={busy}><LoginFields change={change} />
      <button disabled={busy} type="submit">{busy ? 'Memproses…' : change ? 'Simpan password baru' : 'Masuk'}</button>
    </form>
    {change && <button className="secondary" disabled={busy} onClick={() => void exit()}>Keluar</button>}
  </section>
}
function AuthIntro({ change }: { change: boolean }) {
  return <><h1 id="auth-title">{change ? 'Ganti password Anda' : 'Masuk ke Kevin Assurance'}</h1><p>{change ? 'Akun Anda perlu password baru sebelum dapat mengakses data jaminan. Setelah berhasil, masuk kembali.' : 'Gunakan akun yang diberikan oleh administrator.'}</p></>
}
function LoginFields({ change }: { change: boolean }) {
  return <>
    {!change && <label>Username atau email<input name="username" autoComplete="username" spellCheck={false} required maxLength={254} /></label>}
    <label>{change ? 'Password saat ini' : 'Password'}<input name={change ? 'current_password' : 'password'} type="password" autoComplete="current-password" required /></label>
    {change && <label>Password baru<input name="new_password" type="password" autoComplete="new-password" required minLength={8} aria-describedby="password-help" /></label>}
    {change && <p id="password-help">Minimal 8 karakter, berbeda dari password saat ini, bukan password umum atau seluruhnya angka. Pemeriksaan akhir dilakukan server.</p>}
  </>
}
