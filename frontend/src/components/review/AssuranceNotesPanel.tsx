import { useId, useRef } from 'react'
import type { RefObject } from 'react'
import { MessageSquarePlus, RefreshCw } from 'lucide-react'
import { useAuth } from '../../auth/authState'
import { useAssuranceNotes } from '../../hooks/useAssuranceNotes'
import type { AssuranceDetail } from '../../types/assurance'
import { formatJakartaTime, humanRoleLabel } from '../../utils/roleLabels'

function NotesList({ notes, loading, loadError, reload }: {
  notes: ReturnType<typeof useAssuranceNotes>['notes']
  loading: boolean
  loadError: string
  reload: () => void
}) {
  if (loading && !notes.length) return <p role="status" className="muted">Memuat catatan pengajuan…</p>
  if (loadError) {
    return (
      <div role="alert" className="error">
        <p>{loadError}</p>
        <button type="button" className="secondary" onClick={reload}>Muat ulang catatan</button>
      </div>
    )
  }
  if (!notes.length) return <p className="muted">Belum ada catatan pada pengajuan ini.</p>
  return (
    <ol className="notes-thread">
      {notes.map(note => (
        <li key={note.id} className="note-entry">
          <div className="note-meta">
            <span className={`badge note-role-${note.author_role}`}>{humanRoleLabel(note.author_role)}</span>
            <strong>{note.author_username}</strong>
            <time dateTime={note.created_at}>{formatJakartaTime(note.created_at)}</time>
          </div>
          <p className="note-body">{note.message}</p>
        </li>
      ))}
    </ol>
  )
}

function NoteComposer({
  inputId,
  inputRef,
  state,
}: {
  inputId: string
  inputRef: RefObject<HTMLTextAreaElement | null>
  state: ReturnType<typeof useAssuranceNotes>
}) {
  return (
    <form className="note-form" noValidate onSubmit={event => { event.preventDefault(); void state.submit() }}>
      <label htmlFor={inputId}>Tambahkan catatan</label>
      <textarea
        id={inputId}
        ref={inputRef}
        name="assurance_note"
        maxLength={1000}
        rows={3}
        value={state.message}
        disabled={state.busy}
        placeholder="Tulis catatan atau jawaban terkait pengajuan ini…"
        onChange={event => state.setMessage(event.target.value)}
      />
      <div className="note-form-footer">
        <small className="muted">{state.message.length}/1000 karakter</small>
        <button type="submit" disabled={state.busy}>
          <MessageSquarePlus size={16} aria-hidden="true" />{state.busy ? 'Mengirim…' : 'Kirim catatan'}
        </button>
      </div>
      {state.submitError && <p role="alert" className="error">{state.submitError}</p>}
      {state.success && <p role="status" className="notice success-notice">{state.success}</p>}
    </form>
  )
}

export function AssuranceNotesPanel({ detail }: { detail: AssuranceDetail }) {
  const { user } = useAuth()
  const headingId = useId()
  const inputId = useId()
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const state = useAssuranceNotes(detail.id, () => inputRef.current?.focus())
  const partnerBlocked = !detail.dealer.is_active && (user?.role === 'DEALER' || user?.role === 'AGENT')

  return (
    <section className="panel notes-panel" aria-labelledby={headingId}>
      <div className="notes-header">
        <div>
          <h2 id={headingId}>Catatan pengajuan ({state.notes.length})</h2>
          <p className="muted">Komunikasi dua arah antar pihak terkait pada cabang dealer ini dan dapat dipantau Super Admin.</p>
        </div>
        <button type="button" className="secondary" disabled={state.loading || state.busy} onClick={() => void state.reload()}>
          <RefreshCw size={15} aria-hidden="true" />Muat ulang
        </button>
      </div>
      <NotesList notes={state.notes} loading={state.loading} loadError={state.loadError} reload={() => void state.reload()} />
      {partnerBlocked
        ? <p className="notice">Dealer nonaktif: akun Dealer dan Agent hanya dapat membaca histori catatan.</p>
        : <NoteComposer inputId={inputId} inputRef={inputRef} state={state} />}
    </section>
  )
}
