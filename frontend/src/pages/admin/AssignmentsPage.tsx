import { useState } from 'react'
import { useResource } from '../../hooks/useResource'
import type { Assignment, ManagedUser } from '../../types/master'
import type { Dealer } from '../../types/dealer'
import { Feedback } from '../../components/shared/Feedback'
import { DataTable } from '../../components/shared/DataTable'
import { AssignmentEditor } from '../../components/master/AssignmentEditor'
import { DeleteConfirmation } from '../../components/shared/DeleteConfirmation'
import { useSearchParams } from 'react-router-dom'
import { MasterSetupFlow } from '../../components/master/MasterSetupFlow'

export function AssignmentsPage() {
  const resource = useResource<Assignment[]>('dealers/assignments/'), users = useResource<ManagedUser[]>('auth/manage/', true), dealers = useResource<Dealer[]>('dealers/')
  const [editing, setEditing] = useState<Assignment | 'new' | null>(null), [removing, setRemoving] = useState<Assignment | null>(null)
  const ready = users.data && dealers.data
  const [params] = useSearchParams()
  const selectedAgent = users.data?.find(u => u.id === params.get('agent') && u.role === 'AGENT')
  return <section aria-busy={resource.loading}><div className="page-heading"><h1>Penugasan agent</h1><button disabled={!ready} onClick={() => setEditing('new')}>Tambah penugasan</button></div>
    <MasterSetupFlow current="assignment" />
    <p>Hubungkan akun Agent yang sudah dibuat dengan dealer binaannya. Satu Agent dapat memiliki beberapa penugasan.</p>
    <AssignmentNotice user={selectedAgent} />
    <Feedback {...resource} retry={resource.reload} /><Feedback {...users} retry={users.reload} /><Feedback {...dealers} retry={dealers.reload} />
    {resource.data && !resource.data.length && <p className="panel">Belum ada penugasan.</p>}
    {resource.data && resource.data.length > 0 && <DataTable<Assignment> rows={resource.data} label="Daftar penugasan agent" columns={[
      { label: 'Agent', render: a => a.agent_username }, { label: 'Dealer', render: a => a.dealer_name },
      { label: 'Aksi', render: a => <div className="actions"><button className="secondary" disabled={!ready} aria-label={`Ubah penugasan ${a.agent_username} ${a.dealer_name}`} onClick={() => setEditing(a)}>Ubah</button><button className="secondary" aria-label={`Hapus penugasan ${a.agent_username} ${a.dealer_name}`} onClick={() => setRemoving(a)}>Hapus</button></div> },
    ]} />}
    {editing && users.data && dealers.data && <AssignmentEditor initial={editing === 'new' ? undefined : editing} preferredAgent={selectedAgent?.id} agents={users.data.filter(u => u.role === 'AGENT')} dealers={dealers.data} close={() => setEditing(null)} done={resource.reload} />}
    {removing && <DeleteConfirmation path={`dealers/assignments/${removing.id}/`} label="penugasan agent" close={() => setRemoving(null)} done={resource.reload} />}
  </section>
}
function AssignmentNotice({ user }: { user?: ManagedUser }) {
  if (!user) return null
  return <p className="notice">Akun {user.username} siap ditugaskan. Pilih Tambah penugasan, lalu tentukan dealer binaannya.</p>
}
