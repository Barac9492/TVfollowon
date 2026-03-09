import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { fetchCompanies, fetchDashboardStats } from '../api/companies'
import type { CompanyFilters } from '../types'

export function useCompanies() {
  const [searchParams, setSearchParams] = useSearchParams()

  const filters: CompanyFilters = {
    search: searchParams.get('search') || undefined,
    stage: searchParams.get('stage') || undefined,
    score: searchParams.get('score') || undefined,
    status: searchParams.get('status') || undefined,
    has_growth_data: searchParams.get('has_growth_data') || undefined,
    sort_by: searchParams.get('sort_by') || 'score_value',
    sort_dir: (searchParams.get('sort_dir') as 'asc' | 'desc') || 'desc',
    page: Number(searchParams.get('page')) || 1,
    per_page: 50,
  }

  const query = useQuery({
    queryKey: ['companies', filters],
    queryFn: () => fetchCompanies(filters),
  })

  const setFilter = (key: string, value: string | undefined) => {
    const newParams = new URLSearchParams(searchParams)
    if (value) {
      newParams.set(key, value)
    } else {
      newParams.delete(key)
    }
    // Reset to page 1 when filters change
    if (key !== 'page') newParams.delete('page')
    setSearchParams(newParams)
  }

  return { ...query, filters, setFilter }
}

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: fetchDashboardStats,
  })
}
