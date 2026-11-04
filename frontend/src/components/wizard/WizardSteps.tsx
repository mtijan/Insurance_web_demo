import { steps } from '../../utils/wizardSteps'
export function WizardSteps({ current }: { current: number }) { return <ol className="wizard-steps" aria-label="Langkah pengajuan">{steps.map((step, index) => <li key={step} aria-current={current === index ? 'step' : undefined}><span>{index + 1}</span>{step}</li>)}</ol> }
