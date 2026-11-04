import type { AssuranceDetail } from '../../types/assurance'

export function DocumentChecklist({ detail }: { detail: AssuranceDetail }) {
  const missing = new Set(detail.missing_documents.map(type => type.toUpperCase()))
  return <section className="panel" aria-label="Kelengkapan dokumen"><h2>Kelengkapan dokumen</h2>
    <ul className="document-checklist">{detail.required_documents.map(type => <li key={type}><span>{type.replaceAll(' OR ', ' ATAU ').replaceAll('_', ' ')}</span><strong>{missing.has(type.toUpperCase()) ? 'Belum lengkap' : 'Tersedia di server'}</strong></li>)}</ul>
    <p>{detail.is_documents_complete ? 'Seluruh prasyarat dokumen lengkap menurut pemeriksaan server terakhir.' : 'Pengajuan belum dapat dikirim. Kembali ke Dokumen untuk melengkapi berkas.'}</p>
  </section>
}
