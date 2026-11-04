import { useEffect, useState } from 'react'
import { useResource } from './useResource'
import type { DraftFields, Premium } from '../types/wizard'
import { validateFields } from '../schemas/assurance'

export function usePremiumCalculator(values: DraftFields) {
  const query = new URLSearchParams({ sum_insured: values.sum_insured, coverage_type: values.coverage_type, tenor_years: values.tenor_years }).toString()
  const [debounced, setDebounced] = useState(query)
  useEffect(() => { const timer = setTimeout(() => setDebounced(query), 300); return () => clearTimeout(timer) }, [query])
  const valid = !Object.keys(validateFields(values, ['sum_insured', 'coverage_type', 'tenor_years'])).length
  const resource = useResource<Premium>(valid && debounced === query ? `assurances/calculate-premium/?${debounced}` : '')
  return { ...resource, data: valid && debounced === query ? resource.data : undefined, loading: valid && (query !== debounced || resource.loading), valid }
}
