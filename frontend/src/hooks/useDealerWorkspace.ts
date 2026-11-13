import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useResource } from './useResource'
import type { Dealer } from '../types/dealer'
import type { AssuranceRow } from '../types/assurance'

function buildAssuranceQuery(dealerId: string, params: URLSearchParams) {
  if (!dealerId) return ''
  const query = new URLSearchParams()
  query.set('dealer_id', dealerId)
  for (const key of ['status', 'date_from', 'date_to']) {
    const value = params.get(key)
    if (value) query.set(key, value)
  }
  return `assurances/?${query}`
}

export function useDealerWorkspace() {
  const [params, setParams] = useSearchParams()
  const [search, setSearch] = useState('')
  const dealers = useResource<Dealer[]>('dealers/?summary=true')
  const requestedId = params.get('dealer') ?? params.get('dealer_id') ?? ''
  const selected = dealers.data?.find(dealer => dealer.id === requestedId)
  const invalid = Boolean(dealers.data && requestedId && !selected)
  const assurances = useResource<AssuranceRow[]>(buildAssuranceQuery(selected?.id ?? '', params))
  const term = search.trim().toLocaleLowerCase()
  const filteredDealers = (dealers.data ?? []).filter(dealer => `${dealer.code} ${dealer.name}`.toLocaleLowerCase().includes(term))
  function selectDealer(id: string) {
    const next = new URLSearchParams(params)
    next.delete('dealer_id')
    if (id) next.set('dealer', id); else next.delete('dealer')
    setParams(next)
  }
  return { params, search, setSearch, dealers, filteredDealers, selected, invalid, assurances, selectDealer }
}
