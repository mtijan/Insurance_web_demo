import { useParams } from 'react-router-dom'
import type { AssuranceDetail } from '../types/assurance'
import { useResource } from '../hooks/useResource'
import { Feedback } from '../components/shared/Feedback'
import { AssuranceWizard } from '../components/wizard/AssuranceWizard'

export function AssuranceFormPage() {
  const { id } = useParams()
  if (id) return <ExistingDraft key={id} id={id} />
  return <AssuranceWizard key="new" />
}
function ExistingDraft({ id }: { id: string }) {
  const resource = useResource<AssuranceDetail>(`assurances/${id}/`)
  if (!resource.data) return <section><h1>Lanjutkan pengajuan</h1><Feedback {...resource} retry={resource.reload} /></section>
  return <AssuranceWizard initial={resource.data} />
}
