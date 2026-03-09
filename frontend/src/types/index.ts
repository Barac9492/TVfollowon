export interface ActionItem {
  type: 'missing_data' | 'low_score' | 'opportunity'
  field: string
  potential_points: number
  label: string
  detail: string
  priority: 'high' | 'medium' | 'low'
  factor: string
}

export interface Company {
  id: string
  company_name: string
  representative_name: string | null
  current_valuation: number | null
  current_currency: string
  valuation_usd: number | null
  current_stage: string | null
  deal_status: string | null
  batch: string | null
  sector: string | null
  traffic_score: 'green' | 'yellow' | 'red'
  score_value: number
  comment_count: number
  has_growth_data: number
  growth_data_completeness: number
  mrr_growth_rate_pct: number | null
  runway_months: number | null
  monthly_revenue: number | null
  investors: string | null
  top_action_items: ActionItem[]
}

export interface GrowthMetrics {
  id: number
  metric_date: string | null
  monthly_revenue: number | null
  revenue_currency: string | null
  arr: number | null
  mrr: number | null
  revenue_at_first_meeting: number | null
  mrr_growth_rate_pct: number | null
  monthly_burn: number | null
  cash_on_hand: number | null
  runway_months: number | null
  headcount: number | null
  paying_customers: number | null
  ndr_pct: number | null
  key_metric_value: number | null
  key_metric_name: string | null
  last_funding_date: string | null
  last_funding_amount: number | null
  last_funding_round: string | null
  investors: string | null
  notes: string | null
}

export interface CompanyDetail extends Company {
  score_details: string | null
  created_at: string | null
  updated_at: string | null
  comments: Comment[]
  metric_snapshots: MetricSnapshot[]
  growth_metrics: GrowthMetrics[]
  action_items: ActionItem[]
}

export interface Comment {
  id: number
  comment_text: string
  company_name: string | null
  created_at: string | null
}

export interface MetricSnapshot {
  id: number
  valuation: number | null
  currency: string | null
  stage: string | null
  status: string | null
  snapshot_date: string | null
}

export interface CompanyListResponse {
  items: Company[]
  total: number
  page: number
  per_page: number
}

export interface DashboardStats {
  total_companies: number
  green_count: number
  yellow_count: number
  red_count: number
  by_stage: Record<string, number>
  by_status: Record<string, number>
  avg_valuation_usd: number | null
  growth_data_count: number
  avg_mrr_growth: number | null
  funding_window_count: number
}

export interface UploadResponse {
  upload_id: number
  filename: string
  file_type: string
  rows_parsed: number
  rows_created: number
  rows_updated: number
  errors: string[]
}

export interface UploadHistoryItem {
  id: number
  filename: string
  file_type: string | null
  rows_parsed: number
  rows_created: number
  rows_updated: number
  uploaded_at: string | null
}

export interface SlackStatus {
  connected: boolean
  workspace_name?: string
  message?: string
}

export interface Investor {
  name: string
  round?: string
  role?: 'lead' | 'follow' | 'unknown'
}

export interface ResearchStatus {
  enabled: boolean
  message: string
}

export interface ResearchResult {
  research_id: number
  metrics: Record<string, unknown>
  notes: string | null
  sources: { url: string; title: string }[]
  confidence: 'high' | 'medium' | 'low'
}

export interface ResearchLogItem {
  id: number
  company_id: string
  research_type: 'text_extraction' | 'web_research'
  status: 'pending' | 'approved' | 'rejected'
  extracted_metrics: string | null
  created_at: string | null
}

export interface CompanyFilters {
  search?: string
  stage?: string
  score?: string
  status?: string
  has_growth_data?: string
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
  page?: number
  per_page?: number
}
