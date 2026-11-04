import type { InputHTMLAttributes } from 'react'
interface Props extends InputHTMLAttributes<HTMLInputElement> { label: string; error?: string; hint?: string }
export function Field({ label, error, hint, id, name, ...input }: Props) {
  const key = id ?? name
  return <label htmlFor={key}><span id={`${key}-label`}>{label}</span><input {...input} name={name} id={key} aria-labelledby={`${key}-label`} aria-invalid={!!error} aria-describedby={error ? `${key}-error` : hint ? `${key}-hint` : undefined} />{hint && <small id={`${key}-hint`} className="muted">{hint}</small>}{error && <small id={`${key}-error`} className="field-error">{error}</small>}</label>
}
