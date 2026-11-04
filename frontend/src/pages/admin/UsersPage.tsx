import { useState } from 'react'
import { useResource } from '../../hooks/useResource'
import type { ManagedUser } from '../../types/master'
import type { Dealer } from '../../types/dealer'
import { Feedback } from '../../components/shared/Feedback'
import { DataTable } from '../../components/shared/DataTable'
import { UserEditor } from '../../components/master/UserEditor'
import { DeleteConfirmation } from '../../components/shared/DeleteConfirmation'
import { Link, useSearchParams } from 'react-router-dom'
import { MasterSetupFlow } from '../../components/master/MasterSetupFlow'

export function UsersPage() {
  const resource = useResource<ManagedUser[]>('auth/manage/', true), dealers = useResource<Dealer[]>('dealers/')
  const [editing, setEditing] = useState<ManagedUser | 'new' | null>(null), [removing, setRemoving] = useState<ManagedUser | null>(null)
  const [created, setCreated] = useState<ManagedUser | null>(null)
  const [params] = useSearchParams()
  const defaultDealer = dealers.data?.find(d => d.id === params.get('dealer'))
  return <section aria-busy={resource.loading}><div className="page-heading"><h1>Pengguna</h1><button disabled={!dealers.data} onClick={() => setEditing('new')}>Tambah pengguna</button></div>
    <MasterSetupFlow current="user" />
    {defaultDealer && <p className="notice">Siapkan akun Dealer untuk {defaultDealer.name}. Pilih Tambah pengguna untuk melanjutkan.</p>}
    <CreatedAccountNotice user={created} />
    <p>Password awal diberikan oleh Super Admin. Pengguna wajib menggantinya saat login. Nonaktif/reset mencabut sesi lama.</p>
    <Feedback {...resource} retry={resource.reload} /><Feedback {...dealers} retry={dealers.reload} />
    {resource.data && !resource.data.length && <p className="panel">Belum ada pengguna.</p>}
    {!!resource.data?.length && <DataTable rows={resource.data} label="Daftar pengguna" columns={[
      { label: 'Username', render: u => u.username }, { label: 'Email', render: u => u.email }, { label: 'Role / dealer', render: u => `${u.role} · ${u.dealer_name ?? 'Tanpa dealer'}` },
      { label: 'Status', render: u => `${u.is_active ? 'Aktif' : 'Nonaktif'}${u.must_change_password ? ' · Wajib ganti password' : ''}` },
      { label: 'Aksi', render: u => <div className="actions"><button className="secondary" disabled={!dealers.data} onClick={() => setEditing(u)}>Ubah {u.username}</button><button className="secondary" onClick={() => setRemoving(u)}>Hapus {u.username}</button></div> },
    ]} />}
    {editing && dealers.data && <UserEditor initial={editing === 'new' ? undefined : editing} defaultDealer={defaultDealer?.id} onCreated={setCreated} dealers={dealers.data} close={() => setEditing(null)} done={resource.reload} />}
    {removing && <DeleteConfirmation path={`auth/manage/${removing.id}/`} label={`pengguna ${removing.username}`} close={() => setRemoving(null)} done={resource.reload} />}
  </section>
}
function CreatedAccountNotice({ user }: { user: ManagedUser | null }) {
  if (!user) return null
  return <p role="status">Akun {user.username} berhasil dibuat. {user.role === 'AGENT' && <Link to={`/admin/assignments?agent=${user.id}`}>Lanjutkan penugasan Agent {user.username}</Link>}</p>
}
