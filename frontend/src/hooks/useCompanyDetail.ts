import { useQuery } from '@tanstack/react-query'
import { fetchCompanyDetail } from '../api/companies'

export function useCompanyDetail(id: string) {
  return useQuery({
    queryKey: ['company', id],
    queryFn: () => fetchCompanyDetail(id),
    enabled: !!id,
  })
}
