import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchBinary, saveBlob } from '../../services/downloads'
import { useOperation } from '../../hooks/useOperation'

export function ExcelExportButton() {
  const [params] = useSearchParams(), [success, setSuccess] = useState(false), operation = useOperation()
  async function download() {
    setSuccess(false)
    const result = await operation.run(signal => fetchBinary(`assurances/export-excel/?${params}`, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', signal))
    if (result.ok) {
      saveBlob(result.data, 'rekapitulasi-jaminan.xlsx'); setSuccess(true)
    }
  }
  return <div className="panel"><button disabled={operation.busy} onClick={() => void download()}>{operation.busy ? 'Menyiapkan Excel…' : 'Unduh Excel sesuai filter'}</button>{operation.error && <p role="alert" className="error">{operation.error}</p>}{success && <p role="status">Berkas Excel diterima dari server dan unduhan dimulai.</p>}</div>
}
