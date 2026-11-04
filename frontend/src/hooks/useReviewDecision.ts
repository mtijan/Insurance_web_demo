import { useState } from 'react'
import { api } from '../services/apiClient'
import { useOperation } from './useOperation'
import type { AssuranceDetail } from '../types/assurance'
import type { Envelope } from '../types/auth'

export function useReviewDecision(id: string, reload: () => Promise<unknown>) {
  const operation = useOperation()
  const [decision, setDecision] = useState<'APPROVE' | 'REQUEST_REVISION' | 'REJECT_FINAL' | null>(null)
  const [notes, setNotes] = useState(''), [success, setSuccess] = useState('')
  const [mustReload, setMustReload] = useState(false)
  async function submit() {
    if (decision !== 'APPROVE' && !notes.trim()) { operation.setError('Alasan perbaikan atau penolakan wajib diisi.'); return }
    setSuccess('')
    const result = await operation.run(async signal => {
      const response = await api.post<Envelope<AssuranceDetail>>(`assurances/${id}/review/`, { decision, review_notes: notes }, { signal })
      return response.data.data
    })
    if (result.ok) {
      setSuccess(result.data.status === 'ACTIVE' ? `Jaminan aktif. Nomor: ${result.data.assurance_number}` : result.data.status === 'REJECTED' ? 'Pengajuan ditolak final. Alasan tersimpan.' : 'Permintaan perbaikan tersimpan. Status: Perlu perbaikan.')
      setDecision(null); setNotes(''); await reload()
    } else setMustReload(true)
  }
  async function refresh() { await reload(); setMustReload(false); setDecision(null); operation.setError('') }
  return { ...operation, decision, setDecision, notes, setNotes, success, mustReload, submit, refresh }
}
