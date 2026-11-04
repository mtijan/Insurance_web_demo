import type { useWizardSession } from '../../hooks/useWizardSession'
import { steps } from '../../utils/wizardSteps'
import { ConfirmDialog } from '../shared/ConfirmDialog'
type Props = { session: ReturnType<typeof useWizardSession> }

export function WizardActions({ session }: Props) {
  const { fields, actions, busy, editable } = session
  if (!editable) return null
  return <div className="actions">
    <button className="secondary" disabled={busy || fields.step === 0} onClick={() => fields.setStep(n => n - 1)}>Kembali</button>
    <NextStep session={session} />
    {fields.step >= 2 && <button className="secondary" disabled={busy || actions.uncertain} onClick={() => void actions.save()}>{actions.busy ? 'Memproses…' : 'Simpan draft'}</button>}
    <SubmitStep session={session} />
  </div>
}
function NextStep({ session: { fields, actions, busy } }: Props) {
  if (fields.step >= 4) return null
  const locked = busy || (fields.step >= 2 && fields.dirty) || (fields.step === 2 && !actions.detail)
  return <button disabled={locked} onClick={() => { if (fields.valid()) fields.setStep(n => n + 1) }}>Lanjut ke {steps[fields.step + 1]}</button>
}
function SubmitStep({ session: { fields, locked, setConfirm } }: Props) {
  if (fields.step !== 4) return null
  return <><button disabled={locked} aria-describedby="submit-reason" onClick={() => setConfirm(true)}>Kirim untuk verifikasi</button><p id="submit-reason">{locked ? 'Simpan perubahan dan lengkapi seluruh dokumen di server; tunggu unggah selesai sebelum mengirim.' : 'Seluruh prasyarat tersedia. Periksa ringkasan sebelum mengirim.'}</p></>
}
export function SubmitConfirmation({ session: { confirm, busy, setConfirm, locked, actions } }: Props) {
  if (!confirm) return null
  return <ConfirmDialog title="Kirim pengajuan?" busy={busy} close={() => setConfirm(false)}><p>Pengajuan akan dikunci selama verifikasi. Nomor baru diterbitkan setelah disetujui Admin.</p><button disabled={locked} onClick={async () => { await actions.submit(); setConfirm(false) }}>Konfirmasi kirim</button></ConfirmDialog>
}
