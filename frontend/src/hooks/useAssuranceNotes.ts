import { useCallback, useEffect, useState } from 'react'
import { errorMessage } from '../services/apiClient'
import { createAssuranceNote, fetchAssuranceNotes } from '../services/notes'
import { notifyNotificationsChanged } from '../services/notifications'
import type { AssuranceNote } from '../types/note'

function useNoteLoader(assuranceId: string) {
  const [notes, setNotes] = useState<AssuranceNote[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const fetchNotes = useCallback(async (signal?: AbortSignal) => {
    try {
      const data = await fetchAssuranceNotes(assuranceId, signal)
      if (!signal?.aborted) { setNotes(data); setLoadError('') }
    } catch (failure) {
      if (!signal?.aborted) setLoadError(errorMessage(failure))
    } finally {
      if (!signal?.aborted) setLoading(false)
    }
  }, [assuranceId])
  const reload = useCallback(async () => { setLoading(true); setLoadError(''); await fetchNotes() }, [fetchNotes])
  useEffect(() => {
    const controller = new AbortController()
    queueMicrotask(() => { if (!controller.signal.aborted) void fetchNotes(controller.signal) })
    return () => controller.abort()
  }, [fetchNotes])
  return { notes, setNotes, loading, loadError, reload }
}

export function useAssuranceNotes(assuranceId: string, focusInput?: () => void) {
  const { notes, setNotes, loading, loadError, reload } = useNoteLoader(assuranceId)
  const [submitError, setSubmitError] = useState('')
  const [success, setSuccess] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit() {
    const cleaned = message.trim()
    if (!cleaned) { setSubmitError('Catatan tidak boleh kosong.'); setSuccess(''); focusInput?.(); return }
    setBusy(true); setSubmitError(''); setSuccess('')
    try {
      const created = await createAssuranceNote(assuranceId, cleaned)
      setNotes(current => [...current, created]); setMessage('')
      setSuccess('Catatan berhasil dikirim.'); notifyNotificationsChanged()
    } catch (failure) { setSubmitError(errorMessage(failure)) }
    finally { setBusy(false) }
  }

  return { notes, loading, loadError, submitError, success, message, setMessage, busy, reload, submit }
}
