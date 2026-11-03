import axios from 'axios'

export const api = axios.create({ baseURL: '/api/v1/', withCredentials: true, timeout: 20000 })
let csrfToken = ''
export function setCsrfToken(token: string) { csrfToken = token }
api.interceptors.request.use(async config => {
  if (!['get', 'head', 'options'].includes(config.method ?? 'get')) {
    if (!csrfToken) {
      const response = await api.get('auth/csrf/')
      csrfToken = response.data.data.csrf_token
    }
    config.headers['X-CSRFToken'] = csrfToken
  }
  return config
})
api.interceptors.response.use(response => response, error => {
  if (error.response?.status === 401) window.dispatchEvent(new Event('auth-expired'))
  if (error.response?.data?.error_code === 'PASSWORD_CHANGE_REQUIRED') {
    window.dispatchEvent(new Event('password-required'))
  }
  return Promise.reject(error)
})
export function errorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) return 'Terjadi kesalahan. Silakan coba lagi.'
  if (!error.response) return 'Koneksi gagal. Periksa jaringan lalu coba lagi.'
  if (error.response.status === 503) return 'Layanan sementara tidak tersedia. Silakan coba lagi.'
  const errors = error.response.data?.errors
  if (errors && typeof errors === 'object') {
    return Object.entries(errors).map(([field, messages]) =>
      `${field === 'detail' ? '' : `${field}: `}${Array.isArray(messages) ? messages.join(' ') : messages}`,
    ).join(' ')
  }
  return error.response.data?.message ?? 'Permintaan gagal. Silakan coba lagi.'
}
