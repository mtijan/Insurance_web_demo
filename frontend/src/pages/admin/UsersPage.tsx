import { useState } from 'react'
import { useResource } from '../../hooks/useResource'
import type { ManagedUser } from '../../types/master'
import type { Dealer } from '../../types/dealer'
import { Feedback } from '../../components/shared/Feedback'
import { DataTable } from '../../components/shared/DataTable'
import { UserEditor } from '../../components/master/UserEditor'
import { DeleteConfirmation } from '../../components/shared/DeleteConfirmation'
import { Link, useSearchParams } from 'react-router-dom'
import { Pencil, Trash2 } from 'lucide-react'
import { IconAction } from '../../components/shared/IconAction'

export function UsersPage() {
  const resource = useResource<ManagedUser[]>('auth/manage/', true), dealers = useResource<Dealer[]>('dealers/')
  const [editing, setEditing] = useState<ManagedUser | 'new' | null>(null), [removing, setRemoving] = useState<ManagedUser | null>(null)
  const [created, setCreated] = useState<ManagedUser | null>(null)
  const [params] = useSearchParams()
  const defaultDealer = dealers.data?.find(d => d.id === params.get('dealer'))
  return <section aria-busy={resource.loading}><div className="page-heading"><div><p className="eyebrow">Master data</p><h1>Pengguna</h1></div><button disabled={!dealers.data} onClick={() => setEditing('new')}>Tambah pengguna</button></div>
    {defaultDealer && <p className="notice">Siapkan akun Dealer untuk {defaultDealer.name}. Pilih Tambah pengguna untuk melanjutkan.</p>}
    <CreatedAccountNotice user={created} />
    <p>Password awal diberikan oleh Super Admin. Pengguna wajib menggantinya saat login. Nonaktif/reset mencabut sesi lama.</p>
    <Feedback {...resource} retry={resource.reload} /><Feedback {...dealers} retry={dealers.reload} />
    {resource.data && !resource.data.length && <p className="panel">Belum ada pengguna.</p>}
    {!!resource.data?.length && <DataTable rows={resource.data} label="Daftar pengguna" columns={[
      { label: 'Username', render: u => u.username }, { label: 'Email', render: u => u.email }, { label: 'Role / dealer', render: u => <span className="code-badge">{`${u.role} · ${u.dealer_name ?? 'Tanpa dealer'}`}</span> },
      { label: 'Status', render: u => <UserStatusBadge user={u} /> },
      { label: 'Aksi', render: u => <div className="actions"><IconAction label={`Ubah ${u.username}`} icon={Pencil} disabled={!dealers.data} onClick={() => setEditing(u)} /><IconAction label={`Hapus ${u.username}`} icon={Trash2} danger onClick={() => setRemoving(u)} /></div> },
    ]} />}
    {editing && dealers.data && <UserEditor initial={editing === 'new' ? undefined : editing} defaultDealer={defaultDealer?.id} onCreated={setCreated} dealers={dealers.data} close={() => setEditing(null)} done={resource.reload} />}
    {removing && <DeleteConfirmation path={`auth/manage/${removing.id}/`} label={`pengguna ${removing.username}`} close={() => setRemoving(null)} done={resource.reload} />}
  </section>
}
function UserStatusBadge({ user }: { user: ManagedUser }) {
  const tone = !user.is_active ? 'status-INACTIVE' : user.must_change_password ? 'status-REVISION' : 'status-ACTIVE'
  return <span className={`badge ${tone}`}>{`${user.is_active ? 'Aktif' : 'Nonaktif'}${user.must_change_password ? ' · Wajib ganti password' : ''}`}</span>
}
function CreatedAccountNotice({ user }: { user: ManagedUser | null }) {
  if (!user) return null
  return <p role="status" className="notice success-notice">Akun {user.username} berhasil dibuat. {user.role === 'AGENT' && <Link to={`/admin/assignments?agent=${user.id}`}>Lanjutkan penugasan Agent {user.username}</Link>}</p>
}
