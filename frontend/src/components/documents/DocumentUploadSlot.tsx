import { useDocumentSlot } from '../../hooks/useDocumentSlot'
import type { Document } from '../../types/assurance'
import { UploadFeedback } from './UploadFeedback'
import { useState } from 'react'
import { ConfirmDialog } from '../shared/ConfirmDialog'

interface Props {
  assuranceId: string
  type: string
  documents: Document[]
  editable: boolean
  reload: () => Promise<void>
  activity?: (busy: boolean) => void
}
export function DocumentUploadSlot({ assuranceId, type, documents, editable, reload, activity }: Props) {
  const state = useDocumentSlot(assuranceId, type, reload, activity)
  const { busy, setImageError, input, upload, remove } = state
  const [removing, setRemoving] = useState<string | null>(null)
  const label = type.replaceAll('_', ' ')
  return <section className={`document-slot ${documents.length ? 'ready' : 'missing'}`} aria-label={label} aria-busy={busy}>
    <h3>{label}</h3>
    <p>{documents.length ? 'Sudah diunggah' : 'Belum diunggah'}</p>
    {documents.map((document, index) => <figure key={document.id}>
      <a href={`/api/v1/assurances/${assuranceId}/documents/${document.id}/view/`} target="_blank" rel="noreferrer">Buka {label} {index + 1} (tab baru)</a>
      <img width={300} height={200} loading="lazy" src={`/api/v1/assurances/${assuranceId}/documents/${document.id}/view/`} alt={`Pratinjau ${label} ${index + 1}`} onError={() => setImageError(true)} />
      {editable && <button className="secondary" disabled={busy} onClick={() => setRemoving(document.id)} aria-label={`Hapus ${label} ${index + 1}`}>Hapus berkas</button>}
    </figure>)}
    {editable && <label>Unggah {label}<input ref={input} type="file" accept="image/jpeg,image/png,image/webp" disabled={busy} onChange={event => void upload(event.target.files?.[0])} /></label>}
    <UploadFeedback state={state} label={label} editable={editable} />
    {removing && <ConfirmDialog title={`Hapus berkas ${label}?`} busy={busy} close={() => setRemoving(null)}><p>Berkas ini akan dihapus dari draft. Unggah pengganti terlebih dahulu bila diperlukan.</p>{state.error && <p role="alert" className="error">{state.error}</p>}<button disabled={busy} onClick={async () => { if (await remove(removing)) setRemoving(null) }}>Konfirmasi hapus berkas</button></ConfirmDialog>}
  </section>
}
