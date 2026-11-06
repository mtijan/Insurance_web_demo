import { useEffect, useRef, useState } from 'react'
import { api, errorMessage } from '../services/apiClient'
import { compressImage } from '../utils/imageCompressor'
import { uploadDocument } from '../services/documents'
import { useDocumentPreviews } from './documentPreviewState'
import type { OriginalPreview } from './documentPreviewState'

export function useDocumentSlot(assuranceId: string, type: string, reload: () => Promise<void>, activity?: (busy: boolean) => void) {
  const [busy, setBusy] = useState(false), [progress, setProgress] = useState(0), [error, setError] = useState('')
  const [imageError, setImageError] = useState(false), [saved, setSaved] = useState(false)
  const [preview, setPreview] = useState<OriginalPreview>()
  const { previews, create, keep, release, remove: removePreview } = useDocumentPreviews()
  const input = useRef<HTMLInputElement>(null), selected = useRef<File | undefined>(undefined)
  const running = useRef<AbortController | null>(null)
  const candidate = useRef<OriginalPreview | undefined>(undefined)
  useEffect(() => () => { running.current?.abort(); if (candidate.current) release(candidate.current) }, [release])
  async function upload(file?: File) {
    if (!file || running.current) return
    selected.current = file
    const controller = new AbortController(); running.current = controller
    setBusy(true); activity?.(true); setError(''); setProgress(0); setSaved(false); setImageError(false)
    if (candidate.current) { release(candidate.current); candidate.current = undefined }
    setPreview(undefined)
    try {
      const result = await compressImage(file)
      controller.signal.throwIfAborted()
      const original = create(file); candidate.current = original; setPreview(original)
      const uploaded = await uploadDocument(assuranceId, type, result.file, controller.signal, setProgress)
      controller.signal.throwIfAborted()
      keep(uploaded.document_id, original); candidate.current = undefined
      setSaved(true); selected.current = undefined
      if (input.current) input.current.value = ''
      await reload(); setImageError(false)
    } catch (failure) {
      if (!controller.signal.aborted) setError(failure instanceof Error && !('isAxiosError' in failure) ? failure.message : errorMessage(failure))
    } finally { running.current = null; setBusy(false); activity?.(false) }
  }
  async function remove(id: string) {
    if (running.current) return
    const controller = new AbortController(); running.current = controller
    setBusy(true); activity?.(true); setError(''); setSaved(false)
    try { await api.delete(`assurances/${assuranceId}/documents/${id}/`, { signal: controller.signal }); await reload(); if (previews[id]?.url === preview?.url) setPreview(undefined); removePreview(id); return true }
    catch (failure) { if (!controller.signal.aborted) setError(errorMessage(failure)); return false }
    finally { running.current = null; setBusy(false); activity?.(false) }
  }
  return { busy, progress, error, imageError, setImageError, input, upload, remove, retry: () => upload(selected.current), saved, preview }
}
