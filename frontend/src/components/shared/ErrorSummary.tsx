import { useEffect, useRef } from 'react'
import type { FieldErrors } from '../../types/wizard'

export function ErrorSummary({ errors, attempt }: { errors: FieldErrors; attempt: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const entries = Object.entries(errors).filter(([, message]) => !!message)
  useEffect(() => { if (attempt) ref.current?.focus() }, [attempt])
  if (!entries.length) return null
  return <div className="error" role="alert" tabIndex={-1} ref={ref}><p>Periksa isian berikut:</p><ul>{entries.map(([key, message]) => <li key={key}><a href={`#${key}`} onClick={event => { event.preventDefault(); document.getElementById(key)?.focus() }}>{message}</a></li>)}</ul></div>
}
