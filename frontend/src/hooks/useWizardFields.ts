import { useState } from 'react'
import type { AssuranceDetail } from '../types/assurance'
import type { DraftFields, FieldErrors } from '../types/wizard'
import { draftValues } from '../services/assurances'
import { stepFields, validateFields } from '../schemas/assurance'

export function useWizardFields(initial?: AssuranceDetail, accountDealerId?: string) {
  const [values, setValues] = useState(() => draftValues(initial, accountDealerId))
  const [saved, setSaved] = useState(() => JSON.stringify(draftValues(initial, accountDealerId)))
  const [errors, setErrors] = useState<FieldErrors>({})
  const [attempt, setAttempt] = useState(0)
  const [step, setStep] = useState(0)
  function change(key: keyof DraftFields, value: string) {
    setValues(current => ({ ...current, [key]: value }))
    setErrors(current => { const next = { ...current }; delete next[key]; return next })
  }
  function validate(key: keyof DraftFields) {
    const message = validateFields(values, [key])[key]
    setErrors(current => { const next = { ...current }; if (message) next[key] = message; else delete next[key]; return next })
  }
  function valid(all = false) {
    const found = validateFields(values, all ? undefined : stepFields[step] ?? [])
    setErrors(found); setAttempt(n => n + 1)
    if (Object.keys(found).length && all) setStep(stepFields.findIndex(keys => keys.includes(Object.keys(found)[0] as keyof DraftFields)))
    return !Object.keys(found).length
  }
  function accept(detail: AssuranceDetail) {
    const next = draftValues(detail); setValues(next); setSaved(JSON.stringify(next)); setErrors({})
  }
  return { values, errors, attempt, step, setStep, change, validate, valid, accept, dirty: JSON.stringify(values) !== saved }
}
