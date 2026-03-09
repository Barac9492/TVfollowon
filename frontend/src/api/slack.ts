import { apiFetch } from './client'
import type { SlackStatus } from '../types'

export function fetchSlackStatus(): Promise<SlackStatus> {
  return apiFetch('/slack/status')
}

export function fetchSlackMessages(companyId: string) {
  return apiFetch<{ user_name: string; text: string; posted_at: string }[]>(
    `/slack/messages/${companyId}`
  )
}

export function fetchSlackSummary(companyId: string) {
  return apiFetch<{ summary_text: string; message_count: number; generated_at: string } | null>(
    `/slack/summary/${companyId}`
  )
}

export function syncSlack(companyId: string) {
  return apiFetch(`/slack/sync/${companyId}`, { method: 'POST' })
}
