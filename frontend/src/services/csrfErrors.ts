const messages: Record<string, string> = {
  COOKIE_MISSING: 'Cookie keamanan tidak diterima server. Pastikan cookie diizinkan untuk alamat aplikasi ini, lalu coba lagi.',
  TOKEN_MISSING: 'Token keamanan tidak diterima server. Muat ulang halaman dan coba lagi.',
  TOKEN_MISMATCH: 'Token keamanan sudah berubah. Coba lagi; jika tetap gagal, gunakan jendela Incognito/Private.',
  TOKEN_INVALID: 'Token keamanan tidak valid. Muat ulang halaman dan coba lagi.',
  ORIGIN_REJECTED: 'Alamat browser ditolak pemeriksaan keamanan. Buka URL Aplikasi yang dicetak terminal runner.',
  REFERER_REJECTED: 'Asal permintaan tidak dapat diverifikasi. Buka URL aplikasi secara langsung dan coba lagi.',
  UNKNOWN: 'Verifikasi keamanan sesi gagal. Muat ulang halaman dan coba lagi. Pastikan cookie diizinkan untuk alamat aplikasi ini.',
}
export function csrfErrorMessage(data: unknown): string {
  if (!data || typeof data !== 'object') return ''
  const detail = data as { error_code?: unknown; message?: unknown; csrf_reason?: unknown }
  if (detail.error_code !== 'CSRF_FAILED' && detail.message !== 'CSRF verification failed.') return ''
  const code = typeof detail.csrf_reason === 'string' && Object.hasOwn(messages, detail.csrf_reason)
    ? detail.csrf_reason : 'UNKNOWN'
  return `${messages[code]} Kode: CSRF_${code}.`
}
