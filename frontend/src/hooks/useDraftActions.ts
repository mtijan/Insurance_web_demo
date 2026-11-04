import { useState } from 'react'
import axios from 'axios'
import { api, errorMessage } from '../services/apiClient'
import { getAssurance, saveDraft } from '../services/assurances'
import type { AssuranceDetail } from '../types/assurance'
import { useOperation } from './useOperation'
import type { useWizardFields } from './useWizardFields'

export function useDraftActions(fields: ReturnType<typeof useWizardFields>, initial?: AssuranceDetail) {
  const [detail, setDetail] = useState(initial)
  const [notice, setNotice] = useState('')
  const [uncertain, setUncertain] = useState(false)
  const operation = useOperation()
  async function save() {
    if (!fields.valid(true) || uncertain) return
    setNotice('')
    const result = await operation.run(async () => saveDraft(fields.values, detail?.id))
    if (result.ok) { setDetail(result.data); fields.accept(result.data); setNotice('Draft tersimpan di server.'); fields.setStep(3) }
    else if ('failure' in result && axios.isAxiosError(result.failure) && !result.failure.response && !detail) setUncertain(true)
  }
  async function reload() {
    if (!detail) return
    try { const latest = await getAssurance(detail.id); setDetail(latest); return latest }
    catch (failure) { operation.setError(errorMessage(failure)); setDetail(current => current ? { ...current, can_edit: false } : current); return undefined }
  }
  async function submit() {
    if (!detail || fields.dirty) return
    setNotice('')
    const result = await operation.run(async () => {
      await api.post(`assurances/${detail.id}/submit/`)
      return getAssurance(detail.id)
    })
    if (result.ok) { setDetail(result.data); setNotice('Pengajuan berhasil dikirim untuk verifikasi.') }
    else { operation.setError('Hasil pengiriman belum dapat dipastikan. Muat ulang status sebelum mencoba lagi.'); await reload() }
  }
  return { detail, notice, uncertain, ...operation, save, reload, submit }
}
