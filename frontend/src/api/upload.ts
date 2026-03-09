import { apiUpload, apiFetch } from './client'
import type { UploadResponse, UploadHistoryItem } from '../types'

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '') + '/api/v1'

export function uploadPortfolio(file: File): Promise<UploadResponse> {
  return apiUpload('/upload/portfolio', file)
}

export function uploadComments(file: File): Promise<UploadResponse> {
  return apiUpload('/upload/comments', file)
}

export function uploadGrowthData(file: File): Promise<UploadResponse> {
  return apiUpload('/upload/growth', file)
}

export function fetchUploadHistory(): Promise<UploadHistoryItem[]> {
  return apiFetch('/upload/history')
}

export async function downloadGrowthTemplate(): Promise<void> {
  const res = await fetch(`${BASE_URL}/upload/growth-template`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'growth_template.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

export async function downloadGrowthTemplatePrefilled(): Promise<void> {
  const res = await fetch(`${BASE_URL}/upload/growth-template-prefilled`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'growth_template_prefilled.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}
