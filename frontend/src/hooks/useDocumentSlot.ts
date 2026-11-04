import { useEffect, useRef, useState } from 'react'
import { api, errorMessage } from '../services/apiClient'
import { compressImage } from '../utils/imageCompressor'
import type { CompressionMetrics } from '../utils/imageCompressor'
import { uploadDocument } from '../services/documents'

export function useDocumentSlot(assuranceId: string, type: string, reload: () => Promise<void>, activity?: (busy: boolean) => void) {
  const [busy, setBusy] = useState(false), [progress, setProgress] = useState(0), [error, setError] = useState('')
  const [imageError, setImageError] = useState(false), [saved, setSaved] = useState(false)
  const [metrics, setMetrics] = useState<CompressionMetrics>(), [preview, setPreview] = useState('')
  const input = useRef<HTMLInputElement>(null), selected = useRef<File | undefined>(undefined)
  const running = useRef<AbortController | null>(null)
  useEffect(() => () => running.current?.abort(), [])
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])
  async function upload(file?: File) {
    if (!file || running.current) return
    selected.current = file
    const controller = new AbortController(); running.current = controller
    setBusy(true); activity?.(true); setError(''); setProgress(0); setSaved(false)
    try {
      const result = await compressImage(file)
      if (controller.signal.aborted) return
      setMetrics(result.metrics); setPreview(URL.createObjectURL(result.file))
      await uploadDocument(assuranceId, type, result.file, controller.signal, setProgress)
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
    try { await api.delete(`assurances/${assuranceId}/documents/${id}/`, { signal: controller.signal }); await reload(); setPreview(''); setMetrics(undefined); return true }
    catch (failure) { if (!controller.signal.aborted) setError(errorMessage(failure)); return false }
    finally { running.current = null; setBusy(false); activity?.(false) }
  }
  return { busy, progress, error, imageError, setImageError, input, upload, remove, retry: () => upload(selected.current), metrics, saved, preview }
}
