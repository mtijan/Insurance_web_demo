import { useState } from 'react'
import { useAuth } from '../auth/authState'
import { useResource } from '../hooks/useResource'
import type { Dealer } from '../types/dealer'
import { Feedback } from '../components/shared/Feedback'
import { DataTable } from '../components/shared/DataTable'
import { DealerEditor } from '../components/master/DealerEditor'
import { DeleteConfirmation } from '../components/shared/DeleteConfirmation'
import { Pencil, Trash2, UserPlus } from 'lucide-react'
import { IconAction } from '../components/shared/IconAction'
import { dealerTitle } from '../utils/roleLabels'
import type { Role } from '../types/auth'

export function DealersPage() {
  const { user } = useAuth(), resource = useResource<Dealer[]>('dealers/')
  const [editing, setEditing] = useState<Dealer | 'new' | null>(null), [removing, setRemoving] = useState<Dealer | null>(null)
  const owner = user?.role === 'SUPER_ADMIN'
  return <section aria-busy={resource.loading}><div className="page-heading"><DealerHeading role={user?.role} />{owner && <button onClick={() => setEditing('new')}>Tambah dealer</button>}</div>
    <p>{owner ? 'Kelola data dealer dan akun yang terhubung.' : 'Informasi dealer yang dapat Anda akses. Pengelolaan dilakukan oleh Super Admin.'}</p><Feedback {...resource} retry={resource.reload} />
    {resource.data && !resource.data.length && <p className="panel">Belum ada dealer dalam lingkup akun.</p>}
    {!!resource.data?.length && <DataTable rows={resource.data} label="Daftar dealer" columns={[
      { label: 'Kode', render: d => <span className="code-badge">{d.code}</span> }, { label: 'Nama', render: d => d.name }, { label: 'Status', render: d => <span className={`badge ${d.is_active ? 'status-ACTIVE' : 'status-INACTIVE'}`}>{d.is_active ? 'Aktif' : 'Nonaktif'}</span> },
      { label: 'Aksi', render: d => owner ? <div className="actions"><IconAction label={`Buat akun Dealer ${d.code}`} icon={UserPlus} to={`/admin/users?dealer=${d.id}`} /><IconAction label={`Ubah ${d.code}`} icon={Pencil} onClick={() => setEditing(d)} /><IconAction label={`Hapus ${d.code}`} icon={Trash2} danger onClick={() => setRemoving(d)} /></div> : <span className="badge">Hanya baca</span> },
    ]} />}
    {editing && <DealerEditor initial={editing === 'new' ? undefined : editing} close={() => setEditing(null)} done={resource.reload} />}
    {removing && <DeleteConfirmation path={`dealers/${removing.id}/`} label={`dealer ${removing.code}`} close={() => setRemoving(null)} done={resource.reload} />}
  </section>
}
function DealerHeading({ role }: { role?: Role }) {
  return <div><p className="eyebrow">{role === 'SUPER_ADMIN' ? 'Master data' : 'Operasional'}</p><h1>{dealerTitle(role)}</h1></div>
}
