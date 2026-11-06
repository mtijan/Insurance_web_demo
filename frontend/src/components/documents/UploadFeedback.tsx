import type { useDocumentSlot } from '../../hooks/useDocumentSlot'
type Props = { state: ReturnType<typeof useDocumentSlot>; label: string; editable: boolean; showPreview: boolean }

export function UploadFeedback({ state, label, editable, showPreview }: Props) {
  return <>
    {state.imageError && <p role="status">Pratinjau tidak tersedia. Pilih ulang berkas untuk melihat pratinjau.</p>}
    {showPreview && state.preview && <figure><img width={300} height={200} src={state.preview.url} alt={`Pratinjau file asli ${label}`} /><figcaption>{state.preview.name}</figcaption></figure>}
    {state.busy && <label>Progres {label}<progress max={100} value={state.progress} />{state.progress}% · {state.progress === 100 ? 'Menunggu konfirmasi server' : 'Memproses'}</label>}
    {state.saved && <p role="status">Berkas tersimpan di server.</p>}
    {state.error && <p role="alert" className="error">{state.error}</p>}
    {state.error && editable && <button className="secondary" disabled={state.busy} onClick={() => void state.retry()}>Coba lagi {label}</button>}
  </>
}
