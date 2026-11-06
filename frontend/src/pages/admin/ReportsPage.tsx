import { AssuranceFilters } from '../../components/assurances/AssuranceFilters'
import { ExcelExportButton } from '../../components/export/ExcelExportButton'

export function ReportsPage() {
  return <section><div className="page-heading"><div><p className="eyebrow">Administrasi</p><h1>Laporan Excel</h1></div></div><p>Ekspor khusus Super Admin. Filter tanggal memakai tanggal pembuatan pengajuan, inklusif dalam WIB. Bukan tanggal terbit jaminan.</p><AssuranceFilters dates /><ExcelExportButton /></section>
}
