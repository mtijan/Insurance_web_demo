import type { Premium } from '../../types/wizard'
import { money } from '../../utils/format'

export function PremiumSummaryCard({ premium, snapshot = false }: { premium: Premium; snapshot?: boolean }) {
  return <section className="premium-card" aria-label="Ringkasan biaya"><h3>{snapshot ? 'Biaya draft tersimpan (server)' : 'Simulasi biaya dari server'}</h3><dl className="data-grid"><div><dt>Premi murni</dt><dd>{money(premium.base_premium)}</dd></div><div><dt>Biaya admin{snapshot ? ' (snapshot)' : ' saat ini'}</dt><dd>{money(premium.admin_fee)}</dd></div><div><dt>Total premi</dt><dd><strong>{money(premium.total_premium)}</strong></dd></div></dl><p className="muted">{snapshot ? 'Nilai final mengikuti hasil simpan server.' : 'Simulasi bukan keputusan underwriting. Draft existing mempertahankan biaya admin snapshot; periksa hasil setelah menyimpan.'}</p></section>
}
