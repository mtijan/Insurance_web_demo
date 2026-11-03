import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, errorMessage } from '../services/apiClient'
import { DocumentUploadSlot } from '../components/documents/DocumentUploadSlot'
import type { AssuranceDetail } from '../types/assurance'

export function AssuranceDetailPage() {
  const { id } = useParams()
  const [detail, setDetail] = useState<AssuranceDetail | null>(null)
  const [error, setError] = useState('')
  const reload = useCallback(async () => {
    try {
      const response = await api.get(`assurances/${id}/`)
      setDetail(response.data.data); setError('')
    }
    catch (failure) { setError(errorMessage(failure)) }
  }, [id])
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      try {
        const response = await api.get(`assurances/${id}/`, { signal: controller.signal })
        setDetail(response.data.data); setError('')
      } catch (failure) { if (!controller.signal.aborted) setError(errorMessage(failure)) }
    }
    void load()
    return () => controller.abort()
  }, [id])
  const current = detail?.id === id ? detail : null
  const types = current ? [...new Set([...current.required_documents.flatMap(type => type.split(' OR ')), ...current.documents.map(document => document.document_type)])] : []
  return <section>
    <Link to="/">Kembali ke daftar jaminan</Link>
    <h1>Dokumen jaminan</h1>
    {error && <div role="alert"><p className="error">{error}</p><button onClick={() => void reload()}>Coba lagi</button></div>}
    {!current && !error && <p role="status">Memuat detail…</p>}
    {current && <>
      <h2>{current.policy_holder.full_name}</h2><p>Status: {current.status}</p>
      {current.status === 'ACTIVE' && <a className="download" href={`/api/v1/assurances/${id}/summary-pdf/`}>Unduh ringkasan jaminan (PDF)</a>}
      <p>JPEG, PNG, atau WebP maksimal 5 MiB per berkas. Untuk mengganti berkas, unggah pengganti terlebih dahulu, lalu hapus berkas lama.</p>
      {!current.can_edit && <p>Dokumen hanya dapat dibaca pada akun atau status ini.</p>}
      <div className="document-grid">{types.map(type => <DocumentUploadSlot key={type} assuranceId={current.id} type={type} documents={current.documents.filter(document => document.document_type === type)} editable={current.can_edit} reload={reload} />)}</div>
    </>}
  </section>
}
