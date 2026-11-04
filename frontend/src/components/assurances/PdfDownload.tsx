import { useState } from 'react'
import { errorMessage } from '../../services/apiClient'
import { fetchBinary, saveBlob } from '../../services/downloads'

export function PdfDownload({ id }: { id: string }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('')
  async function download() {
    if (busy) return
    setBusy(true); setError('')
    try {
      const blob = await fetchBinary(`assurances/${id}/summary-pdf/`, 'application/pdf')
      saveBlob(blob, 'ringkasan-jaminan.pdf')
    } catch (failure) { setError(errorMessage(failure)) } finally { setBusy(false) }
  }
  return <><button disabled={busy} onClick={() => void download()}>{busy ? 'Menyiapkan PDF…' : 'Unduh ringkasan jaminan (PDF)'}</button>{error && <p role="alert" className="error">{error}</p>}</>
}
