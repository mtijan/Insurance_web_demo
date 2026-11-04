import type { useDocumentSlot } from '../../hooks/useDocumentSlot'
type Props = { state: ReturnType<typeof useDocumentSlot>; label: string; editable: boolean }

export function UploadFeedback({ state, label, editable }: Props) {
  return <>
    {state.imageError && <p role="status">Pratinjau tidak tersedia. Coba muat ulang halaman.</p>}
    <CompressionPreview state={state} label={label} />
    {state.busy && <label>Progres {label}<progress max={100} value={state.progress} />{state.progress}% · {state.progress === 100 ? 'Menunggu konfirmasi server' : 'Memproses'}</label>}
    {state.saved && <p role="status">Berkas tersimpan di server.</p>}
    {state.error && <p role="alert" className="error">{state.error}</p>}
    {state.error && editable && <button className="secondary" disabled={state.busy} onClick={() => void state.retry()}>Coba lagi {label}</button>}
  </>
}
function CompressionPreview({ state: { preview, metrics }, label }: Pick<Props, 'state' | 'label'>) {
  return <>{preview && <img width={300} height={200} loading="lazy" src={preview} alt={`Pratinjau hasil kompresi ${label}`} />}
    {metrics && <p className="compression-metrics">{metrics.beforeBytes} → {metrics.afterBytes} byte; {metrics.beforeWidth}×{metrics.beforeHeight} → {metrics.afterWidth}×{metrics.afterHeight}px. Pengurangan {Math.round((1 - metrics.afterBytes / metrics.beforeBytes) * 100)}%. Periksa teks/angka pada hasil.</p>}
  </>
}
