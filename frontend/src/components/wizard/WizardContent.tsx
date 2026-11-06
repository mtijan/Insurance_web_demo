import type { useWizardSession } from '../../hooks/useWizardSession'
import type { Dealer } from '../../types/dealer'
import { StepDealer } from './StepDealer'
import { StepPolicyHolder } from './StepPolicyHolder'
import { StepVehicleDetails } from './StepVehicleDetails'
import { ConditionalDocumentUploader } from '../documents/ConditionalDocumentUploader'
import { AssuranceSummary } from '../assurances/AssuranceSummary'
import { DocumentChecklist } from '../documents/DocumentChecklist'

export function WizardContent({ session, dealer }: { session: ReturnType<typeof useWizardSession>; dealer?: Dealer }) {
  const { fields, actions, activity, busy, editable } = session
  if (!editable && actions.detail) return <><p className="notice">Status {actions.detail.status}: pengajuan hanya dapat dibaca.</p><AssuranceSummary detail={actions.detail} /></>
  const views = [<StepDealer key="dealer" {...fields} dealer={dealer} />, <StepPolicyHolder key="holder" {...fields} />, <StepVehicleDetails key="vehicle" {...fields} />]
  return <form aria-label="Formulir pengajuan" noValidate onSubmit={event => event.preventDefault()}><fieldset disabled={busy}>
    {fields.step < 3 && views[fields.step]}
    {fields.step === 3 && actions.detail && <ConditionalDocumentUploader detail={actions.detail} reload={actions.reload} activity={activity} />}
    {fields.step === 4 && actions.detail && <><AssuranceSummary detail={actions.detail} /><DocumentChecklist detail={actions.detail} /></>}
  </fieldset></form>
}
