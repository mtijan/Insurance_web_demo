import { Link, useLocation } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { useAuth } from '../../auth/authState'
import type { AssuranceDetail } from '../../types/assurance'
import type { Dealer } from '../../types/dealer'
import { useWizardSession } from '../../hooks/useWizardSession'
import { WizardSteps } from './WizardSteps'
import { UnsavedGuard } from './UnsavedGuard'
import { WizardFeedback } from './WizardFeedback'
import { WizardContent } from './WizardContent'
import { WizardActions, SubmitConfirmation } from './WizardActions'
import { DocumentPreviewProvider } from '../documents/DocumentPreviewProvider'
import { assuranceReturnLabel, assuranceReturnPath, safeBackTarget } from '../../utils/roleLabels'

export function AssuranceWizard({ initial, dealer }: { initial?: AssuranceDetail; dealer?: Dealer }) {
  const { user } = useAuth()
  const { state } = useLocation()
  const session = useWizardSession(initial, dealer?.id)
  const fallback = assuranceReturnPath(user?.role, dealer?.id ?? initial?.dealer.id, session.actions.detail?.status ?? initial?.status ?? 'DRAFT')
  const backTo = safeBackTarget(state, fallback)
  return <DocumentPreviewProvider><section aria-busy={session.busy}>
    <div className="page-heading"><div><p className="eyebrow">Operasional</p><h1>{initial ? 'Lanjutkan pengajuan' : 'Buat pengajuan'}</h1></div><Link className="back-link" to={backTo}><ArrowLeft size={16} aria-hidden="true" />{assuranceReturnLabel(user?.role)}</Link></div>
    <UnsavedGuard dirty={session.fields.dirty} busy={session.busy} /><WizardSteps current={session.fields.step} accountDealer={!!dealer} />
    <WizardFeedback session={session} /><WizardContent session={session} dealer={dealer} /><WizardActions session={session} /><SubmitConfirmation session={session} />
  </section></DocumentPreviewProvider>
}
