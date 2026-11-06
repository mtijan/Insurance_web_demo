import type { Premium } from '../../types/wizard'
import { money } from '../../utils/format'
import { premiumSimulation } from '../../utils/premiumSimulation'

export function PremiumSummaryCard({ premium, tenorYears }: { premium: Premium; tenorYears: number }) {
  const simulation = premiumSimulation(premium.total_premium, tenorYears)
  return <section className="premium-card" aria-label="Ringkasan biaya">
    <h3>Perhitungan simulasi biaya</h3>
    <dl className="data-grid"><div><dt>Premi murni</dt><dd>{money(premium.base_premium)}</dd></div><div><dt>Biaya admin</dt><dd>{money(premium.admin_fee)}</dd></div><div><dt>Total premi</dt><dd><strong>{money(premium.total_premium)}</strong></dd></div></dl>
    <dl className="data-grid premium-periods"><div><dt>Estimasi per tahun</dt><dd><strong>{money(simulation.annual)}</strong></dd></div><div><dt>Estimasi per bulan</dt><dd><strong>{money(simulation.monthly)}</strong></dd></div></dl>
    <p className="muted">Simulasi pembagian total premi termasuk biaya admin untuk {tenorYears} tahun ({tenorYears * 12} bulan), dibulatkan hingga dua desimal.</p>
    <p className="muted">Nilai simulasi dapat berbeda dari biaya draft sebelumnya. Periksa kembali ringkasan setelah melanjutkan ke Dokumen.</p>
  </section>
}
