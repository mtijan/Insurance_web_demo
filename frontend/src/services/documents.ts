import { api } from './apiClient'
import type { Envelope } from '../types/auth'

export async function uploadDocument(id: string, type: string, file: File, signal: AbortSignal, progress: (value: number) => void) {
  const data = new FormData(); data.set('document_type', type); data.set('file', file)
  const response = await api.post<Envelope<{ document_id: string }>>(`assurances/${id}/documents/`, data, {
    signal, onUploadProgress: event => progress(Math.min(100, Math.round(event.loaded / (event.total || file.size) * 100))),
  })
  return response.data.data
}
