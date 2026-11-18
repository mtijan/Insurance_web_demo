import { api } from './apiClient'
import type { Envelope } from '../types/auth'
import type { AssuranceNote } from '../types/note'

export async function fetchAssuranceNotes(assuranceId: string, signal?: AbortSignal) {
  const response = await api.get<Envelope<AssuranceNote[]>>(`assurances/${assuranceId}/notes/`, { signal })
  return response.data.data
}

export async function createAssuranceNote(assuranceId: string, message: string, signal?: AbortSignal) {
  const response = await api.post<Envelope<AssuranceNote>>(
    `assurances/${assuranceId}/notes/`,
    { message },
    { signal },
  )
  return response.data.data
}
