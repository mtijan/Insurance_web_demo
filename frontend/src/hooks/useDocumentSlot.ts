import { useRef, useState } from 'react'
import { api, errorMessage } from '../services/apiClient'

async function uploadFile(assuranceId: string, type: string, file: File, progress: (value: number) => void) {
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) {
    throw new Error('Pilih JPEG, PNG, atau WebP maksimal 5 MiB.')
  }
  const data = new FormData()
  data.set('document_type', type); data.set('file', file)
  await api.post(`assurances/${assuranceId}/documents/`, data, {
    onUploadProgress: event => progress(Math.round((event.loaded / (event.total || file.size)) * 100)),
  })
}
export function useDocumentSlot(assuranceId: string, type: string, reload: () => Promise<void>) {
  const [busy, setBusy] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const [imageError, setImageError] = useState(false)
  const input = useRef<HTMLInputElement>(null)
  async function upload(file?: File) {
    if (!file) return
    setBusy(true); setError(''); setProgress(0)
    try {
      await uploadFile(assuranceId, type, file, setProgress)
      if (input.current) input.current.value = ''
      await reload(); setImageError(false)
    } catch (failure) {
      setError(failure instanceof Error && failure.message.startsWith('Pilih JPEG') ? failure.message : errorMessage(failure))
    } finally { setBusy(false) }
  }
  async function remove(id: string) {
    setBusy(true); setError('')
    try { await api.delete(`assurances/${assuranceId}/documents/${id}/`); await reload() }
    catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return { busy, progress, error, imageError, setImageError, input, upload, remove }
}
