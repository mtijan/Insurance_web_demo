import { useEffect, useState } from 'react'
import { api, errorMessage } from '../services/apiClient'

interface Entry { id: string; action: string; entity_name: string; entity_id: string; created_at: string }
export function AuditPage() {
  const [entries, setEntries] = useState<Entry[]>([])
  const [page, setPage] = useState(1)
  const [next, setNext] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(true)
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      try {
        const response = await api.get(`audit/?page=${page}`, { signal: controller.signal })
        setEntries(response.data.data.results); setNext(response.data.data.has_next); setError('')
      } catch (failure) { if (!controller.signal.aborted) setError(errorMessage(failure)) }
      finally { if (!controller.signal.aborted) setBusy(false) }
    }
    void load()
    return () => controller.abort()
  }, [page, attempt])
  function move(step: number) { setBusy(true); setPage(value => value + step) }
  return <section aria-busy={busy}>
    <h1>Riwayat audit</h1>
    <p>Ringkasan aktivitas sistem. Isi perubahan, IP, dan data pribadi tidak ditampilkan.</p>
    {busy && <p role="status">Memuat riwayat…</p>}
    {error && <div role="alert"><p>{error}</p><button onClick={() => { setBusy(true); setAttempt(value => value + 1) }}>Coba lagi</button></div>}
    {!busy && !error && !entries.length && <p>Belum ada catatan audit.</p>}
    <ul className="assurance-list">{!busy && !error && entries.map(entry => <li key={entry.id}>
      <strong>{entry.action} · {entry.entity_name}</strong><span>{entry.entity_id}</span>
      <time dateTime={entry.created_at}>{new Date(entry.created_at).toLocaleString('id-ID')}</time>
    </li>)}</ul>
    <nav aria-label="Halaman audit" className="toolbar">
      <button disabled={busy || page === 1} onClick={() => move(-1)}>Sebelumnya</button>
      <span aria-live="polite">Halaman {page}</span>
      <button disabled={busy || !next} onClick={() => move(1)}>Berikutnya</button>
    </nav>
  </section>
}
