import { useParams, useNavigate } from 'react-router-dom'
import { useCompanyDetail } from '../../hooks/useCompanyDetail'
import CompanyHeader from './CompanyHeader'
import MetricChart from './MetricChart'
import CommentsList from './CommentsList'
import SlackPanel from './SlackPanel'
import ResearchPanel from './ResearchPanel'
import ActionItemsPanel from './ActionItemsPanel'
import type { GrowthMetrics, Investor } from '../../types'
import { formatGrowthRate, formatRunway, formatRevenue, formatDate } from '../../utils/formatters'

export default function CompanyDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: company, isLoading, error } = useCompanyDetail(id!)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900" />
      </div>
    )
  }

  if (error || !company) {
    return (
      <div className="text-center py-20">
        <p className="text-red-500">회사를 찾을 수 없습니다</p>
        <button onClick={() => navigate('/')} className="mt-4 text-sm text-slate-500 underline">
          대시보드로 돌아가기
        </button>
      </div>
    )
  }

  return (
    <div>
      <button
        onClick={() => navigate('/')}
        className="text-sm text-slate-500 hover:text-slate-700 mb-4 flex items-center gap-1"
      >
        ← 대시보드
      </button>

      <CompanyHeader company={company} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <div className="space-y-6">
          {company.action_items && company.action_items.length > 0 && (
            <ActionItemsPanel items={company.action_items} />
          )}
          {company.growth_metrics && company.growth_metrics.length > 0 && (
            <GrowthDataPanel metrics={company.growth_metrics} />
          )}
          <MetricChart snapshots={company.metric_snapshots} currency={company.current_currency} />
          <ScoreBreakdown details={company.score_details} completeness={company.growth_data_completeness} />
        </div>
        <div className="space-y-6">
          <CommentsList comments={company.comments} />
          <ResearchPanel companyId={company.id} companyName={company.company_name} />
          <SlackPanel companyId={company.id} companyName={company.company_name} />
        </div>
      </div>
    </div>
  )
}

function GrowthDataPanel({ metrics }: { metrics: GrowthMetrics[] }) {
  const latest = metrics[0]
  if (!latest) return null

  const items = [
    { label: '월매출', value: formatRevenue(latest.monthly_revenue) },
    { label: 'MRR', value: formatRevenue(latest.mrr) },
    { label: 'ARR', value: formatRevenue(latest.arr) },
    { label: 'MRR 성장률', value: formatGrowthRate(latest.mrr_growth_rate_pct) },
    { label: '월 번', value: formatRevenue(latest.monthly_burn) },
    { label: '보유 현금', value: formatRevenue(latest.cash_on_hand) },
    { label: '런웨이', value: formatRunway(latest.runway_months) },
    { label: '인원', value: latest.headcount != null ? `${latest.headcount}명` : '-' },
    { label: '유료 고객', value: latest.paying_customers != null ? `${latest.paying_customers}` : '-' },
    { label: 'NDR', value: latest.ndr_pct != null ? `${latest.ndr_pct.toFixed(0)}%` : '-' },
  ].filter(item => item.value !== '-')

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-slate-900">성장 데이터</h3>
        <span className="text-xs text-slate-400">
          최신: {formatDate(latest.metric_date)} | {metrics.length}건의 스냅샷
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {items.map((item) => (
          <div key={item.label} className="bg-slate-50 rounded-lg p-3">
            <p className="text-xs text-slate-400">{item.label}</p>
            <p className="text-sm font-semibold text-slate-700 mt-0.5">{item.value}</p>
          </div>
        ))}
      </div>

      {latest.key_metric_name && (
        <div className="mt-3 pt-3 border-t border-slate-100">
          <p className="text-xs text-slate-400">핵심 KPI: {latest.key_metric_name}</p>
          <p className="text-sm font-semibold text-slate-700">
            {latest.key_metric_value != null ? latest.key_metric_value.toLocaleString() : '-'}
          </p>
        </div>
      )}

      {latest.last_funding_round && (
        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-4 text-xs text-slate-500">
          <span>최근 라운드: <strong>{latest.last_funding_round}</strong></span>
          {latest.last_funding_amount && (
            <span>금액: <strong>{formatRevenue(latest.last_funding_amount)}</strong></span>
          )}
          {latest.last_funding_date && (
            <span>일자: {formatDate(latest.last_funding_date)}</span>
          )}
        </div>
      )}

      {latest.investors && (() => {
        try {
          const investors: Investor[] = JSON.parse(latest.investors)
          if (investors.length === 0) return null
          return (
            <div className="mt-3 pt-3 border-t border-slate-100">
              <p className="text-xs text-slate-400 mb-1.5">💰 투자자</p>
              <div className="flex flex-wrap gap-1.5">
                {investors.map((inv, i) => (
                  <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700">
                    {inv.name}{inv.round ? ` (${inv.round})` : ''}
                  </span>
                ))}
              </div>
            </div>
          )
        } catch { return null }
      })()}

      {latest.notes && (
        <p className="mt-3 text-xs text-slate-500 bg-slate-50 rounded p-2">{latest.notes}</p>
      )}
    </div>
  )
}

function ScoreBreakdown({ details, completeness }: { details: string | null; completeness: number }) {
  if (!details) return null

  let parsed: Record<string, { value: number; max?: number; label?: string }>
  try {
    parsed = JSON.parse(details)
  } catch {
    return null
  }

  // New 6-factor scoring
  const factors = ['growth_velocity', 'capital_efficiency', 'funding_urgency', 'deal_status', 'comments', 'stage_valuation']
  const factorNames: Record<string, string> = {
    growth_velocity: '성장 속도',
    capital_efficiency: '자본 효율성',
    funding_urgency: '펀딩 타이밍',
    deal_status: '딜 상태',
    comments: '코멘트',
    stage_valuation: '단계/밸류',
  }

  // Fallback for old scoring format
  const oldFactors = ['status', 'recency', 'stage', 'valuation']
  const isNewFormat = factors.some((f) => parsed[f])

  const displayFactors = isNewFormat ? factors : [...oldFactors, 'comments']
  const oldFactorNames: Record<string, string> = {
    status: '딜 상태', recency: '최신성', stage: '투자 단계', valuation: '밸류에이션', comments: '코멘트',
  }
  const oldMaxValues: Record<string, number> = {
    status: 40, recency: 20, stage: 15, valuation: 10, comments: 15,
  }

  const barColors: Record<string, string> = {
    growth_velocity: 'bg-emerald-500',
    capital_efficiency: 'bg-blue-500',
    funding_urgency: 'bg-amber-500',
    deal_status: 'bg-slate-600',
    comments: 'bg-purple-500',
    stage_valuation: 'bg-indigo-500',
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-slate-900">스코어 상세</h3>
        {completeness > 0 && (
          <span className="text-xs text-slate-400">데이터 완성도: {completeness.toFixed(0)}%</span>
        )}
      </div>
      <div className="space-y-3">
        {displayFactors.map((f) => {
          const item = parsed[f]
          if (!item) return null
          const max = item.max || (isNewFormat ? 30 : oldMaxValues[f] || 20)
          const pct = Math.round((item.value / max) * 100)
          const name = isNewFormat ? factorNames[f] : oldFactorNames[f]
          const barColor = barColors[f] || 'bg-slate-700'
          return (
            <div key={f}>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-600">{name || f}</span>
                <span className="text-slate-500">
                  {item.value}/{max}
                  {item.label ? ` (${item.label})` : ''}
                </span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full ${barColor} rounded-full transition-all`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          )
        })}
        {parsed.total !== undefined && (
          <div className="pt-2 border-t border-slate-100 flex justify-between font-semibold text-sm">
            <span>총점</span>
            <span>{typeof parsed.total === 'object' ? (parsed.total as { value: number }).value : parsed.total}/100</span>
          </div>
        )}
      </div>
    </div>
  )
}
