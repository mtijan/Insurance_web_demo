function dividePremium(total: string, periods: number) {
  const [whole, fraction = ''] = total.split('.')
  const cents = BigInt(whole) * 100n + BigInt(fraction.padEnd(2, '0'))
  const divisor = BigInt(periods)
  const rounded = (cents * 2n + divisor) / (divisor * 2n)
  return `${rounded / 100n}.${String(rounded % 100n).padStart(2, '0')}`
}

export function premiumSimulation(total: string, years: number) {
  return { annual: dividePremium(total, years), monthly: dividePremium(total, years * 12) }
}
