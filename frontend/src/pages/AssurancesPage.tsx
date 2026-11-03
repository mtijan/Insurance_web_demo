import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, errorMessage } from '../services/apiClient'
import type { AssuranceRow } from '../types/assurance'

export function AssurancesPage() {
  const [rows, setRows] = useState<AssuranceRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      try {
        const response = await api.get('assurances/', { signal: controller.signal })
        setRows(response.data.data); setError('')
      }
      catch (failure) { if (!controller.signal.aborted) setError(errorMessage(failure)) }
      finally { if (!controller.signal.aborted) setLoading(false) }
    }
    void load()
    return () => controller.abort()
  }, [attempt])
  return <section>
    <h1>Daftar jaminan</h1>
    <p>Data mengikuti hak akses akun Anda. Pilih jaminan untuk memeriksa dokumen.</p>
    {loading && <p role="status">Memuat jaminan…</p>}
    {error && <div role="alert"><p className="error">{error}</p><button onClick={() => { setLoading(true); setError(''); setAttempt(value => value + 1) }}>Coba lagi</button></div>}
    {!loading && !error && !rows.length && <p>Belum ada jaminan dalam lingkup akun Anda.</p>}
    <ul className="assurance-list">{rows.map(row => <li key={row.id}>
      <Link to={`/assurances/${row.id}`}>{row.policy_holder_name}</Link>
      <span>{row.dealer_name} · {row.status}</span>
      <span>{row.assurance_number ?? 'Nomor belum diterbitkan'}</span>
    </li>)}</ul>
  </section>
}
