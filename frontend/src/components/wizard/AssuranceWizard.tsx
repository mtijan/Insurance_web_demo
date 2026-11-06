import { Link } from 'react-router-dom'
import type { AssuranceDetail } from '../../types/assurance'
import type { Dealer } from '../../types/dealer'
import { useWizardSession } from '../../hooks/useWizardSession'
import { WizardSteps } from './WizardSteps'
import { UnsavedGuard } from './UnsavedGuard'
import { WizardFeedback } from './WizardFeedback'
import { WizardContent } from './WizardContent'
import { WizardActions, SubmitConfirmation } from './WizardActions'

export function AssuranceWizard({ initial, dealer }: { initial?: AssuranceDetail; dealer?: Dealer }) {
  const session = useWizardSession(initial, dealer?.id)
  return <section aria-busy={session.busy}>
    <div className="page-heading"><div><p className="eyebrow">Operasional</p><h1>{initial ? 'Lanjutkan pengajuan' : 'Buat pengajuan'}</h1></div><Link className="back-link" to="/">Kembali ke daftar jaminan</Link></div>
    <UnsavedGuard dirty={session.fields.dirty} busy={session.busy} /><WizardSteps current={session.fields.step} accountDealer={!!dealer} />
    <WizardFeedback session={session} /><WizardContent session={session} dealer={dealer} /><WizardActions session={session} /><SubmitConfirmation session={session} />
  </section>
}
