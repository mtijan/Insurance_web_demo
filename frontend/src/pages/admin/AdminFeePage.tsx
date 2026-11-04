import { useState } from 'react'
import { useResource } from '../../hooks/useResource'
import type { AdminFee } from '../../types/master'
import { Feedback } from '../../components/shared/Feedback'
import { AdminFeeConfigModal } from '../../components/config/AdminFeeConfigModal'
import { money } from '../../utils/format'

export function AdminFeePage() {
  const resource = useResource<AdminFee>('configs/admin-fee/')
  const [open, setOpen] = useState(false), [saved, setSaved] = useState(false)
  async function done() { setSaved(true); await resource.reload() }
  return <section aria-busy={resource.loading}><p className="eyebrow">Administrasi</p><h1>Biaya admin</h1><Feedback {...resource} retry={resource.reload} />
    {saved && <p role="status" className="notice">Konfigurasi berhasil disimpan oleh server.</p>}
    {resource.data && <div className="panel"><h2>Nilai aktif: {money(resource.data.value)}</h2><p>Berlaku pada draft baru dan simulasi. Pengajuan existing memakai snapshot saat dibuat.</p><button onClick={() => { setSaved(false); setOpen(true) }}>Ubah biaya admin</button></div>}
    {open && resource.data && <AdminFeeConfigModal value={resource.data.value} close={() => setOpen(false)} done={done} />}
  </section>
}
