import { useCallback, useEffect, useRef, useState } from 'react'
import type { AssuranceDetail } from '../types/assurance'
import { useWizardFields } from './useWizardFields'
import { useDraftActions } from './useDraftActions'
import { useNavigationSafety } from '../components/layout/navigationSafety'

export function useWizardSession(initial?: AssuranceDetail, accountDealerId?: string) {
  const fields = useWizardFields(initial, accountDealerId), actions = useDraftActions(fields, initial)
  const [uploads, setUploads] = useState(0), [confirm, setConfirm] = useState(false)
  const activity = useCallback((busy: boolean) => setUploads(n => Math.max(0, n + (busy ? 1 : -1))), [])
  const previousStep = useRef(fields.step)
  const busy = actions.busy || uploads > 0
  const { setSafety } = useNavigationSafety()
  useEffect(() => { setSafety({ dirty: fields.dirty, busy }); return () => setSafety({ dirty: false, busy: false }) }, [fields.dirty, busy, setSafety])
  useEffect(() => { const h1 = document.querySelector<HTMLElement>('main h1'); h1?.setAttribute('tabindex', '-1'); h1?.focus() }, [])
  useEffect(() => {
    if (previousStep.current !== fields.step) {
      const heading = document.querySelector<HTMLElement>('main h2')
      heading?.setAttribute('tabindex', '-1'); heading?.focus()
      previousStep.current = fields.step
    }
  }, [fields.step])
  const editable = !actions.detail || actions.detail.can_edit
  const locked = !actions.detail?.is_documents_complete || fields.dirty || busy || !editable
  return { fields, actions, activity, busy, editable, locked, confirm, setConfirm }
}
