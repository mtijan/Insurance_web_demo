import { useRef, useState } from 'react'
import { api } from '../services/apiClient'
import { useOperation } from './useOperation'

export function useInspection(id: string, reload: () => Promise<unknown>) {
  const operation = useOperation()
  const notesRef = useRef<HTMLTextAreaElement>(null)
  const [section, setSection] = useState('DOCUMENTS'), [notes, setNotes] = useState('')
  const [success, setSuccess] = useState(''), [mustReload, setMustReload] = useState(false)
  const [confirmRevision, setConfirmRevision] = useState(false)
  async function submit(action: string, target = section) {
    if (['NOTE', 'REQUEST_REVISION'].includes(action) && !notes.trim()) { operation.setError('Tuliskan bagian yang perlu diperbaiki.'); notesRef.current?.focus(); return }
    setSuccess('')
    const result = await operation.run(async signal => {
      await api.post(`assurances/${id}/inspection/`, { action, section: target, review_notes: notes }, { signal })
    })
    if (result.ok) {
      setMustReload(false)
      setSuccess(action === 'REQUEST_REVISION' ? 'Permintaan perbaikan dikirim ke Dealer.' : 'Hasil peninjauan tersimpan.')
      setNotes(''); setConfirmRevision(false); await reload()
    } else setMustReload(true)
  }
  async function refresh() { await reload(); setMustReload(false); setConfirmRevision(false); operation.setError('') }
  function requestRevision() {
    if (!notes.trim()) { operation.setError('Tuliskan bagian yang perlu diperbaiki.'); notesRef.current?.focus(); return }
    operation.setError(''); setConfirmRevision(true)
  }
  return { ...operation, section, setSection, notes, setNotes, notesRef, requestRevision, success, mustReload, submit, refresh, confirmRevision, setConfirmRevision }
}
