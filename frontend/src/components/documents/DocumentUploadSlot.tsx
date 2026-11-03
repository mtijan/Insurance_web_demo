import { useDocumentSlot } from '../../hooks/useDocumentSlot'
import type { Document } from '../../types/assurance'

interface Props {
  assuranceId: string
  type: string
  documents: Document[]
  editable: boolean
  reload: () => Promise<void>
}
export function DocumentUploadSlot({ assuranceId, type, documents, editable, reload }: Props) {
  const { busy, progress, error, imageError, setImageError, input, upload, remove } = useDocumentSlot(assuranceId, type, reload)
  const label = type.replaceAll('_', ' ')
  return <section className={`document-slot ${documents.length ? 'ready' : 'missing'}`} aria-label={label} aria-busy={busy}>
    <h3>{label}</h3>
    <p>{documents.length ? 'Sudah diunggah' : 'Belum diunggah'}</p>
    {documents.map((document, index) => <figure key={document.id}>
      <a href={`/api/v1/assurances/${assuranceId}/documents/${document.id}/view/`} target="_blank" rel="noreferrer">Buka {label} {index + 1} (tab baru)</a>
      <img src={`/api/v1/assurances/${assuranceId}/documents/${document.id}/view/`} alt={`Pratinjau ${label} ${index + 1}`} onError={() => setImageError(true)} />
      {editable && <button className="secondary" disabled={busy} onClick={() => void remove(document.id)} aria-label={`Hapus ${label} ${index + 1}`}>Hapus berkas</button>}
    </figure>)}
    {imageError && <p role="status">Pratinjau tidak tersedia. Coba muat ulang halaman.</p>}
    {editable && <label>Unggah {label}<input ref={input} type="file" accept="image/jpeg,image/png,image/webp" disabled={busy} onChange={event => void upload(event.target.files?.[0])} /></label>}
    {busy && <label>Progres {label}<progress max={100} value={progress} />{progress}% · Memproses</label>}
    {error && <p role="alert" className="error">{error}</p>}
  </section>
}
