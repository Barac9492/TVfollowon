import { useNavigate } from 'react-router-dom'
import type { Company, Investor } from '../../types'
import TrafficBadge from './TrafficBadge'
import { formatValuation, stageLabel, formatGrowthRate, formatRunway } from '../../utils/formatters'

export default function CompanyCard({ company }: { company: Company }) {
  const navigate = useNavigate()
  const hasGrowth = company.has_growth_data > 0

  return (
    <div
      onClick={() => navigate(`/company/${company.id}`)}
      className="bg-white rounded-xl border border-slate-200 p-5 cursor-pointer hover:shadow-lg hover:border-slate-300 transition-all"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-slate-900 truncate">{company.company_name}</h3>
          <p className="text-sm text-slate-500 truncate">{company.representative_name || '-'}</p>
        </div>
        <TrafficBadge score={company.traffic_score} />
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        {hasGrowth ? (
          <>
            <div>
              <p className="text-xs text-slate-400">MRR 성장</p>
              <p className={`text-sm font-semibold ${
                company.mrr_growth_rate_pct !== null && company.mrr_growth_rate_pct >= 10
                  ? 'text-emerald-600'
                  : company.mrr_growth_rate_pct !== null && company.mrr_growth_rate_pct >= 0
                  ? 'text-slate-700'
                  : 'text-red-600'
              }`}>
                {formatGrowthRate(company.mrr_growth_rate_pct)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400">런웨이</p>
              <p className={`text-sm font-semibold ${
                company.runway_months !== null && company.runway_months <= 6
                  ? 'text-amber-600'
                  : 'text-slate-700'
              }`}>
                {formatRunway(company.runway_months)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400">스코어</p>
              <p className="text-sm font-semibold text-slate-700">{company.score_value}</p>
            </div>
          </>
        ) : (
          <>
            <div>
              <p className="text-xs text-slate-400">밸류에이션</p>
              <p className="text-sm font-semibold text-slate-700">
                {formatValuation(company.current_valuation, company.current_currency)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400">단계</p>
              <p className="text-sm font-semibold text-slate-700">{stageLabel(company.current_stage)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">스코어</p>
              <p className="text-sm font-semibold text-slate-700">{company.score_value}</p>
            </div>
          </>
        )}
      </div>

      {company.top_action_items && company.top_action_items.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2.5">
          {company.top_action_items.map((item, i) => (
            <span
              key={i}
              className={`text-[11px] px-2 py-0.5 rounded-full ${
                item.priority === 'high'
                  ? 'bg-red-50 text-red-600'
                  : item.priority === 'medium'
                  ? 'bg-amber-50 text-amber-600'
                  : 'bg-slate-50 text-slate-500'
              }`}
            >
              {item.priority === 'high' ? '⚠️' : '📋'} {item.label}
            </span>
          ))}
        </div>
      )}

      {company.investors && (() => {
        try {
          const investors: Investor[] = JSON.parse(company.investors)
          if (investors.length === 0) return null
          return (
            <p className="text-xs text-slate-400 mt-2 truncate">
              💰 {investors.map(i => i.name).join(', ')}
            </p>
          )
        } catch { return null }
      })()}

      <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-100">
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            company.deal_status === '트래킹'
              ? 'bg-blue-50 text-blue-700'
              : 'bg-slate-100 text-slate-500'
          }`}>
            {company.deal_status || '-'}
          </span>
          {hasGrowth && (
            <span className="text-xs text-slate-400" title={`데이터 완성도 ${company.growth_data_completeness.toFixed(0)}%`}>
              {company.growth_data_completeness >= 70 ? '📊' : '📉'}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {company.batch && (
            <span className="text-xs text-slate-400">Batch {company.batch}</span>
          )}
          {company.comment_count > 0 && (
            <span className="text-xs text-slate-400">💬 {company.comment_count}</span>
          )}
        </div>
      </div>
    </div>
  )
}
