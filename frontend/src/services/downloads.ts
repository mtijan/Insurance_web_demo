import axios from 'axios'
import { api } from './apiClient'

export async function fetchBinary(path: string, mime: string, signal?: AbortSignal) {
  try {
    const response = await api.get<Blob>(path, { responseType: 'blob', signal })
    if (!String(response.headers['content-type']).startsWith(mime)) throw new Error('Unexpected binary response')
    return response.data
  } catch (failure) {
    if (axios.isAxiosError<Blob | Record<string, unknown>>(failure) && failure.response?.data instanceof Blob) {
      try {
        const parsed: unknown = JSON.parse(await failure.response.data.text())
        if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) failure.response.data = parsed as Record<string, unknown>
      } catch { /* Keep the original HTTP failure if the proxy returned a non-JSON body. */ }
    }
    throw failure
  }
}
export function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob), anchor = document.createElement('a')
  anchor.href = url; anchor.download = filename; anchor.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
