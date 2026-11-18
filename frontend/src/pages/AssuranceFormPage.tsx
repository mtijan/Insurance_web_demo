import { Link, Navigate, useParams, useSearchParams } from 'react-router-dom'
import type { AssuranceDetail } from '../types/assurance'
import { useResource } from '../hooks/useResource'
import { Feedback } from '../components/shared/Feedback'
import { AssuranceWizard } from '../components/wizard/AssuranceWizard'
import { useAuth } from '../auth/authState'
import type { Dealer } from '../types/dealer'
import { isUuidParam, isWorkspaceRole } from '../utils/roleLabels'

export function AssuranceFormPage() {
  const { id } = useParams()
  const { user } = useAuth()
  if (id !== undefined && !isUuidParam(id)) return <section className="panel" role="alert"><h1>Pengajuan jaminan</h1><p>ID pengajuan tidak valid.</p></section>
  if (user?.role === 'DEALER') return <AccountDealerForm key={`${user.id}:${id ?? 'new'}`} id={id} />
  if (isWorkspaceRole(user?.role)) return id ? <ExistingDraft key={id} id={id} bindDealer /> : <WorkspaceDealerForm key={user?.id} />
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
function WorkspaceDealerForm() {
  const [params] = useSearchParams()
  const dealerId = params.get('dealer') ?? ''
  const resource = useResource<Dealer[]>(dealerId ? 'dealers/?active_only=true&summary=true' : '')
  if (!dealerId) return <Navigate to="/dealers" replace />
  const dealer = resource.data?.find(item => item.id === dealerId)
  if (dealer) return <AssuranceWizard key={dealer.id} dealer={dealer} />
  return <section><h1>Buat pengajuan</h1>
    <Feedback {...resource} retry={resource.reload} />
    {resource.data && <div role="alert" className="notice"><p>Dealer yang dipilih tidak tersedia, nonaktif, atau di luar lingkup akun Anda. Pilih dealer melalui workspace terlebih dahulu.</p><Link className="back-link" to="/dealers">Pilih dealer di workspace</Link></div>}
  </section>
}
function ExistingDraft({ id, dealer, bindDealer = false }: { id: string; dealer?: Dealer; bindDealer?: boolean }) {
  const resource = useResource<AssuranceDetail>(`assurances/${id}/`)
  if (!resource.data) return <section><h1>Lanjutkan pengajuan</h1><Feedback {...resource} retry={resource.reload} /></section>
  return <AssuranceWizard initial={resource.data} dealer={dealer ?? (bindDealer ? resource.data.dealer : undefined)} />
}
