import { useSearchParams } from 'react-router-dom'
import { useResource } from './useResource'
import type { AssuranceRow } from '../types/assurance'
import { progressStatuses } from '../utils/statusLabels'

export function useDealerApplications(drafts: boolean) {
  const [params] = useSearchParams()
  const status = params.get('status') ?? ''
  const query = new URLSearchParams()
  if (drafts) query.set('status', 'DRAFT')
  else if (progressStatuses.includes(status)) query.set('status', status)
  const resource = useResource<AssuranceRow[]>(query.size ? `assurances/?${query}` : 'assurances/')
  const rows = (resource.data ?? []).filter(row => drafts ? row.status === 'DRAFT' : row.status !== 'DRAFT')
  return { resource, rows }
}
