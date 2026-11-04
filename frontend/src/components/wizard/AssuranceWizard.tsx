import { Link } from 'react-router-dom'
import type { AssuranceDetail } from '../../types/assurance'
import { useWizardSession } from '../../hooks/useWizardSession'
import { WizardSteps } from './WizardSteps'
import { UnsavedGuard } from './UnsavedGuard'
import { WizardFeedback } from './WizardFeedback'
import { WizardContent } from './WizardContent'
import { WizardActions, SubmitConfirmation } from './WizardActions'

export function AssuranceWizard({ initial }: { initial?: AssuranceDetail }) {
  const session = useWizardSession(initial)
  return <section aria-busy={session.busy}>
    <Link to="/">Kembali ke daftar jaminan</Link><h1>{initial ? 'Lanjutkan pengajuan' : 'Buat pengajuan'}</h1>
    <UnsavedGuard dirty={session.fields.dirty} busy={session.busy} /><WizardSteps current={session.fields.step} />
    <WizardFeedback session={session} /><WizardContent session={session} /><WizardActions session={session} /><SubmitConfirmation session={session} />
  </section>
}
