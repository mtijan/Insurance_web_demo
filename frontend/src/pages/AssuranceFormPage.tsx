import { useParams } from 'react-router-dom'
import type { AssuranceDetail } from '../types/assurance'
import { useResource } from '../hooks/useResource'
import { Feedback } from '../components/shared/Feedback'
import { AssuranceWizard } from '../components/wizard/AssuranceWizard'
import { useAuth } from '../auth/authState'
import type { Dealer } from '../types/dealer'

export function AssuranceFormPage() {
  const { id } = useParams()
  const { user } = useAuth()
  if (user?.role === 'DEALER') return <AccountDealerForm key={`${user.id}:${id ?? 'new'}`} id={id} />
  if (id) return <ExistingDraft key={id} id={id} />
  return <AssuranceWizard key="new" />
}
function AccountDealerForm({ id }: { id?: string }) {
  const resource = useResource<Dealer[]>('dealers/?active_only=true&summary=true')
  if (resource.data?.length === 1) {
    const dealer = resource.data[0]
    return id ? <ExistingDraft id={id} dealer={dealer} /> : <AssuranceWizard dealer={dealer} />
  }
  return <section><h1>{id ? 'Lanjutkan pengajuan' : 'Buat pengajuan'}</h1>
    <Feedback {...resource} retry={resource.reload} />
    {resource.data && <div role="alert" className="notice"><p>Dealer aktif untuk akun ini belum tersedia. Hubungi Admin untuk memeriksa hubungan akun dengan dealer.</p><button className="secondary" onClick={() => void resource.reload()}>Coba lagi</button></div>}
  </section>
}
function ExistingDraft({ id, dealer }: { id: string; dealer?: Dealer }) {
  const resource = useResource<AssuranceDetail>(`assurances/${id}/`)
  if (!resource.data) return <section><h1>Lanjutkan pengajuan</h1><Feedback {...resource} retry={resource.reload} /></section>
  return <AssuranceWizard initial={resource.data} dealer={dealer} />
}
