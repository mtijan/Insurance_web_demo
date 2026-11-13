import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { api, errorMessage } from '../services/apiClient'
import { DataTable } from '../components/shared/DataTable'
import { Feedback } from '../components/shared/Feedback'

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
    <div className="page-heading"><div><p className="eyebrow">Administrasi</p><h1>Riwayat audit</h1></div></div>
    <p>Ringkasan aktivitas sistem. Isi perubahan, IP, dan data pribadi tidak ditampilkan.</p>
    <Feedback loading={busy} error={error} retry={() => { setBusy(true); setAttempt(value => value + 1) }} />
    {!busy && !error && <AuditTable entries={entries} />}
    <nav aria-label="Halaman audit" className="toolbar audit-pagination">
      <button className="secondary" disabled={busy || page === 1} onClick={() => move(-1)}><ChevronLeft size={16} aria-hidden="true" />Sebelumnya</button>
      <span aria-live="polite">Halaman {page}</span>
      <button className="secondary" disabled={busy || !next} onClick={() => move(1)}>Berikutnya<ChevronRight size={16} aria-hidden="true" /></button>
    </nav>
  </section>
}

function AuditTable({ entries }: { entries: Entry[] }) {
  if (!entries.length) return <p className="panel">Belum ada catatan audit.</p>
  return <DataTable rows={entries} label="Daftar riwayat audit" columns={[
    { label: 'Aktivitas', render: entry => <strong>{entry.action} · {entry.entity_name}</strong> },
    { label: 'ID Entitas', render: entry => <span className="code-badge">{entry.entity_id}</span> },
    { label: 'Waktu (WIB)', render: entry => <time className="audit-time" dateTime={entry.created_at}>{new Date(entry.created_at).toLocaleString('id-ID', { timeZone: 'Asia/Jakarta' })} WIB</time> },
  ]} />
}
