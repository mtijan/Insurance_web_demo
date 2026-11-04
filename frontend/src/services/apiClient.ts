import axios from 'axios'
import { csrfErrorMessage } from './csrfErrors'

export const api = axios.create({ baseURL: '/api/v1/', withCredentials: true, timeout: 20000 })
let csrfRequest: Promise<string> | null = null
function currentCsrfToken(): Promise<string> {
  // Login in another tab rotates the cookie. Never retain its matching token.
  // Share an in-flight GET so concurrent first mutations do not race cookies.
  csrfRequest ??= api.get<{ data: { csrf_token: string } }>('auth/csrf/')
    .then(response => response.data.data.csrf_token)
    .finally(() => { csrfRequest = null })
  return csrfRequest
}
api.interceptors.request.use(async config => {
  if (!['get', 'head', 'options'].includes(config.method ?? 'get')) {
    config.headers['X-CSRFToken'] = await currentCsrfToken()
  }
  return config
})
api.interceptors.response.use(response => response, error => {
  if (error.response?.status === 401) window.dispatchEvent(new Event('auth-expired'))
  if (error.response?.status === 403 && !error.config?.url?.startsWith('auth/')) window.dispatchEvent(new Event('permissions-changed'))
  if (error.response?.data?.error_code === 'PASSWORD_CHANGE_REQUIRED') {
    window.dispatchEvent(new Event('password-required'))
  }
  return Promise.reject(error)
})
export function errorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) return 'Terjadi kesalahan. Silakan coba lagi.'
  if (!error.response) return 'Koneksi gagal. Periksa jaringan lalu coba lagi.'
  if (error.response.status === 503) return 'Layanan sementara tidak tersedia. Silakan coba lagi.'
  const csrfMessage = csrfErrorMessage(error.response.data)
  if (csrfMessage) return csrfMessage
  const errors = error.response.data?.errors
  if (errors && typeof errors === 'object') {
    return Object.entries(errors).map(([field, messages]) =>
      `${field === 'detail' ? '' : `${field}: `}${Array.isArray(messages) ? messages.join(' ') : messages}`,
    ).join(' ')
  }
  return error.response.data?.message ?? 'Permintaan gagal. Silakan coba lagi.'
}
