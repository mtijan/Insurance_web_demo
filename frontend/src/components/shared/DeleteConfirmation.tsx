import { useOperation } from '../../hooks/useOperation'
import { api } from '../../services/apiClient'
import { ConfirmDialog } from './ConfirmDialog'

export function DeleteConfirmation({ path, label, close, done }: { path: string; label: string; close: () => void; done: () => Promise<unknown> }) {
  const operation = useOperation()
  return <ConfirmDialog title={`Hapus ${label}?`} close={close} busy={operation.busy}><p>Data yang memiliki referensi histori mungkin dilindungi server. Penonaktifan tersedia melalui Ubah bila sesuai.</p>{operation.error && <p role="alert" className="error">{operation.error}</p>}<button disabled={operation.busy} onClick={async () => { const result = await operation.run(signal => api.delete(path, { signal })); if (result.ok) { await done(); close() } }}>Konfirmasi hapus</button></ConfirmDialog>
}
