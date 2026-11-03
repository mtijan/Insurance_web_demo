import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { useAuth } from './authState'
import { api, errorMessage } from '../services/apiClient'
import { loginSchema, passwordSchema } from '../schemas/auth'

function validationMessage(failure: unknown) {
  return failure && typeof failure === 'object' && 'issues' in failure
    ? (failure.issues as { message: string }[]).map(issue => issue.message).join(' ')
    : errorMessage(failure)
}
export function useAuthForm(change: boolean) {
  const { login, clear } = useAuth()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [completed, setCompleted] = useState(false)
  const errorRef = useRef<HTMLParagraphElement>(null)
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setBusy(true)
    const form = event.currentTarget
    const values = Object.fromEntries(new FormData(form))
    try {
      if (change) {
        await api.post('auth/change-password/', passwordSchema.parse(values))
        form.reset(); setCompleted(true); clear()
      } else {
        const payload = loginSchema.parse(values)
        await login(payload.username, payload.password)
        form.reset()
      }
    } catch (failure) {
      setError(validationMessage(failure))
      requestAnimationFrame(() => errorRef.current?.focus())
    } finally { setBusy(false) }
  }
  async function exit() {
    try { await api.post('auth/logout/'); clear() } catch (failure) { setError(errorMessage(failure)) }
  }
  return { error, busy, errorRef, submit, exit, completed }
}
