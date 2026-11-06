import { useState } from 'react'
import { useResource } from '../../hooks/useResource'
import type { AdminFee } from '../../types/master'
import { Feedback } from '../../components/shared/Feedback'
import { AdminFeeConfigModal } from '../../components/config/AdminFeeConfigModal'
import { money } from '../../utils/format'
import { Pencil } from 'lucide-react'
import { IconAction } from '../../components/shared/IconAction'

export function AdminFeePage() {
  const resource = useResource<AdminFee>('configs/admin-fee/')
  const [open, setOpen] = useState(false), [saved, setSaved] = useState(false)
  async function done() { setSaved(true); await resource.reload() }
  return <section aria-busy={resource.loading}><div className="page-heading"><div><p className="eyebrow">Administrasi</p><h1>Biaya admin</h1></div></div><Feedback {...resource} retry={resource.reload} />
    {saved && <p role="status" className="notice success-notice">Konfigurasi berhasil disimpan oleh server.</p>}
    {resource.data && <div className="panel config-card"><div><h2>Nilai aktif: {money(resource.data.value)}</h2><p>Berlaku pada draft baru dan simulasi. Pengajuan existing memakai snapshot saat dibuat.</p></div><IconAction label="Ubah biaya admin" icon={Pencil} onClick={() => { setSaved(false); setOpen(true) }} /></div>}
    {open && resource.data && <AdminFeeConfigModal value={resource.data.value} close={() => setOpen(false)} done={done} />}
  </section>
}
