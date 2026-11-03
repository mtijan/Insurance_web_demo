import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/authState'
import { useAuthForm } from '../auth/useAuthForm'

export function LoginPage({ change = false }: { change?: boolean }) {
  const { user, loading, error: sessionError } = useAuth()
  const location = useLocation()
  const { error, busy, errorRef, submit, exit, completed } = useAuthForm(change)
  if (loading) return <p role="status">Memeriksa sesi?</p>
  if (change && !user) return <Navigate to={completed ? '/login?changed=1' : '/login'} replace />
  if (!change && user) return <Navigate to={user.must_change_password ? '/change-password' : '/'} replace />
  return <section className="auth-card" aria-labelledby="auth-title">
    <p className="eyebrow">Akses internal</p>
    <h1 id="auth-title">{change ? 'Ganti password Anda' : 'Masuk ke Kevin Assurance'}</h1>
    <p>{change ? 'Akun Anda perlu password baru sebelum dapat mengakses data jaminan. Setelah berhasil, masuk kembali.' : 'Gunakan akun yang diberikan oleh administrator.'}</p>
    {new URLSearchParams(location.search).has('changed') &&
      <p role="status">Password berhasil diganti. Silakan masuk kembali.</p>}
    {(error || sessionError) && <p className="error" role="alert" tabIndex={-1} ref={errorRef}>{error || sessionError}</p>}
    <form onSubmit={submit} aria-busy={busy}>
      {!change && <label>Username atau email<input name="username" autoComplete="username" required maxLength={254} /></label>}
      <label>{change ? 'Password saat ini' : 'Password'}<input name={change ? 'current_password' : 'password'} type="password" autoComplete="current-password" required /></label>
      {change && <label>Password baru<input name="new_password" type="password" autoComplete="new-password" required minLength={8} aria-describedby="password-help" /></label>}
      {change && <p id="password-help">Minimal 8 karakter, berbeda dari password saat ini, bukan password umum atau seluruhnya angka. Pemeriksaan akhir dilakukan server.</p>}
      <button disabled={busy} type="submit">{busy ? 'Memproses…' : change ? 'Simpan password baru' : 'Masuk'}</button>
    </form>
    {change && <button className="secondary" disabled={busy} onClick={() => void exit()}>Keluar</button>}
  </section>
}
