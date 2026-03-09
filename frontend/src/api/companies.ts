import { apiFetch } from './client'
import type { CompanyListResponse, CompanyDetail, DashboardStats, CompanyFilters } from '../types'

export function fetchCompanies(filters: CompanyFilters): Promise<CompanyListResponse> {
  const params = new URLSearchParams()
  if (filters.search) params.set('search', filters.search)
  if (filters.stage) params.set('stage', filters.stage)
  if (filters.score) params.set('score', filters.score)
  if (filters.status) params.set('status', filters.status)
  if (filters.has_growth_data) params.set('has_growth_data', filters.has_growth_data)
  if (filters.sort_by) params.set('sort_by', filters.sort_by)
  if (filters.sort_dir) params.set('sort_dir', filters.sort_dir)
  if (filters.page) params.set('page', String(filters.page))
  if (filters.per_page) params.set('per_page', String(filters.per_page))
  return apiFetch(`/companies?${params.toString()}`)
}

export function fetchCompanyDetail(id: string): Promise<CompanyDetail> {
  return apiFetch(`/companies/${id}`)
}

export function fetchDashboardStats(): Promise<DashboardStats> {
  return apiFetch('/companies/stats')
}
