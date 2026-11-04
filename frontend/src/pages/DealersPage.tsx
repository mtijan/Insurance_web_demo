import { useState } from 'react'
import { useAuth } from '../auth/authState'
import { useResource } from '../hooks/useResource'
import type { Dealer } from '../types/dealer'
import { Feedback } from '../components/shared/Feedback'
import { DataTable } from '../components/shared/DataTable'
import { DealerEditor } from '../components/master/DealerEditor'
import { DeleteConfirmation } from '../components/shared/DeleteConfirmation'

export function DealersPage() {
  const { user } = useAuth(), resource = useResource<Dealer[]>('dealers/')
  const [editing, setEditing] = useState<Dealer | 'new' | null>(null), [removing, setRemoving] = useState<Dealer | null>(null)
  const owner = user?.role === 'SUPER_ADMIN'
  return <section aria-busy={resource.loading}><div className="page-heading"><div><p className="eyebrow">Master data</p><h1>Dealer</h1></div>{owner && <button onClick={() => setEditing('new')}>Tambah dealer</button>}</div>
    <p>Dealer dalam lingkup akun, termasuk yang nonaktif. Mutasi hanya untuk Super Admin.</p><Feedback {...resource} retry={resource.reload} />
    {resource.data && !resource.data.length && <p className="panel">Belum ada dealer dalam lingkup akun.</p>}
    {!!resource.data?.length && <DataTable rows={resource.data} label="Daftar dealer" columns={[
      { label: 'Kode', render: d => d.code }, { label: 'Nama', render: d => d.name }, { label: 'Status', render: d => d.is_active ? 'Aktif' : 'Nonaktif' },
      { label: 'Aksi', render: d => owner ? <div className="actions"><button className="secondary" onClick={() => setEditing(d)}>Ubah {d.code}</button><button className="secondary" onClick={() => setRemoving(d)}>Hapus {d.code}</button></div> : 'Hanya baca' },
    ]} />}
    {editing && <DealerEditor initial={editing === 'new' ? undefined : editing} close={() => setEditing(null)} done={resource.reload} />}
    {removing && <DeleteConfirmation path={`dealers/${removing.id}/`} label={`dealer ${removing.code}`} close={() => setRemoving(null)} done={resource.reload} />}
  </section>
}
