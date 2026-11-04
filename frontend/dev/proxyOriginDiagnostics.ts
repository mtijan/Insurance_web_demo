import type { ProxyOptions } from 'vite'

function safeOrigin(value: unknown): string {
  if (value === undefined) return 'MISSING'
  if (value === 'null') return 'null'
  return typeof value === 'string' && /^https?:\/\/(127\.0\.0\.1|localhost)(:\d{1,5})?$/.test(value)
    ? value : 'OTHER_OR_INVALID'
}
function hostOrigin(value: unknown): string {
  return typeof value === 'string' ? safeOrigin(`http://${value}`) : 'MISSING'
}
export const proxyOriginDiagnostics: NonNullable<ProxyOptions['configure']> = proxy => {
  proxy.on('proxyReq', (outgoing, incoming) => {
    if (incoming.method !== 'POST' || incoming.url !== '/api/v1/auth/login/') return
    console.info(JSON.stringify({ event: 'dev_login_proxy_origin',
      time_wib: new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Jakarta', dateStyle: 'short', timeStyle: 'medium' }).format(new Date()),
      incoming_origin: safeOrigin(incoming.headers.origin),
      forwarded_origin: safeOrigin(outgoing.getHeader('origin')),
      ui_origin: safeOrigin(process.env.UI_BASE_URL),
      incoming_host: hostOrigin(incoming.headers.host),
      forwarded_host: hostOrigin(outgoing.getHeader('host')),
    }))
  })
}
