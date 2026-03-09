import { apiFetch } from './client'
import type { ResearchStatus, ResearchResult, ResearchLogItem } from '../types'

export function fetchResearchStatus(): Promise<ResearchStatus> {
  return apiFetch('/research/status')
}

export function extractFromText(
  companyId: string,
  companyName: string,
  text: string,
): Promise<ResearchResult> {
  return apiFetch('/research/extract', {
    method: 'POST',
    body: JSON.stringify({ company_id: companyId, company_name: companyName, text }),
  })
}

export function webResearch(
  companyId: string,
  companyName: string,
  additionalContext?: string,
): Promise<ResearchResult> {
  return apiFetch('/research/web-search', {
    method: 'POST',
    body: JSON.stringify({
      company_id: companyId,
      company_name: companyName,
      additional_context: additionalContext || '',
    }),
  })
}

export function approveResearch(
  researchId: number,
  metrics: Record<string, unknown>,
): Promise<{ growth_metrics_id: number; company_id: string; message: string }> {
  return apiFetch(`/research/approve/${researchId}`, {
    method: 'POST',
    body: JSON.stringify({ metrics }),
  })
}

export function fetchResearchHistory(companyId: string): Promise<ResearchLogItem[]> {
  return apiFetch(`/research/history/${companyId}`)
}
