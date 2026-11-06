import { useDealerApplications } from '../hooks/useDealerApplications'
import { Feedback } from '../components/shared/Feedback'
import { DealerApplicationFilters } from '../components/assurances/DealerApplicationFilters'
import { DealerApplicationRow } from '../components/assurances/DealerApplicationRow'

const modes = {
  drafts: { title: 'Draft', unit: 'draft', intro: 'Pengajuan yang tersimpan dan belum dikirim. Buka draft untuk melanjutkan pengisian.', empty: 'Belum ada draft', hint: 'Lengkapi form Buat pengajuan, lalu pilih Lanjut ke Dokumen untuk menyimpan draft.' },
  progress: { title: 'Proses pengajuan', unit: 'pengajuan', intro: 'Pantau tahap pemeriksaan, perbaikan yang diminta, dan hasil pengajuan dealer Anda.', empty: 'Tidak ada pengajuan untuk ditampilkan', hint: 'Pengajuan yang sudah dikirim akan muncul di sini. Periksa juga filter status yang dipilih.' },
}

export function DealerApplicationsPage({ drafts = false }: { drafts?: boolean }) {
  const { resource, rows } = useDealerApplications(drafts)
  const mode = drafts ? modes.drafts : modes.progress
  return <section aria-busy={resource.loading}>
    <div className="page-heading"><div><p className="eyebrow">Operasional</p><h1>{mode.title}</h1></div>
      <button className="secondary" disabled={resource.loading} onClick={() => void resource.reload()}>Perbarui status</button>
    </div>
    <p>{mode.intro}</p>
    {!drafts && <DealerApplicationFilters />}
    <Feedback {...resource} retry={resource.reload} />
    {resource.data && !rows.length && <div className="panel"><h2>{mode.empty}</h2><p>{mode.hint}</p></div>}
    <ul className="assurance-list">{rows.map(row => <DealerApplicationRow key={row.id} row={row} />)}</ul>
    {resource.data && <p className="muted">{rows.length} {mode.unit} dimuat dalam lingkup dealer Anda.</p>}
  </section>
}
