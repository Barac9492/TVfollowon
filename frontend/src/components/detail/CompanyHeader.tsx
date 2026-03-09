import type { CompanyDetail } from '../../types'
import TrafficBadge from '../dashboard/TrafficBadge'
import { formatValuation, stageLabel, formatUSD, formatGrowthRate, formatRunway } from '../../utils/formatters'

export default function CompanyHeader({ company }: { company: CompanyDetail }) {
  const hasGrowth = company.has_growth_data > 0

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900">{company.company_name}</h1>
            <TrafficBadge score={company.traffic_score} size="lg" />
          </div>
          <p className="text-slate-500 mt-1">{company.representative_name || '-'}</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-slate-900">
            {formatValuation(company.current_valuation, company.current_currency)}
          </p>
          {company.valuation_usd && (
            <p className="text-sm text-slate-400">{formatUSD(company.valuation_usd)}</p>
          )}
        </div>
      </div>

      <div className={`grid ${hasGrowth ? 'grid-cols-6' : 'grid-cols-4'} gap-4 mt-5 pt-5 border-t border-slate-100`}>
        <MetaItem label="투자 단계" value={stageLabel(company.current_stage)} />
        <MetaItem label="딜 상태" value={company.deal_status || '-'} />
        <MetaItem label="배치" value={company.batch || '-'} />
        <MetaItem label="스코어" value={`${company.score_value}/100`} />
        {hasGrowth && (
          <>
            <MetaItem
              label="MRR 성장률"
              value={formatGrowthRate(company.mrr_growth_rate_pct)}
              highlight={company.mrr_growth_rate_pct !== null && company.mrr_growth_rate_pct >= 10}
            />
            <MetaItem
              label="런웨이"
              value={formatRunway(company.runway_months)}
              warn={company.runway_months !== null && company.runway_months <= 6}
            />
          </>
        )}
      </div>
    </div>
  )
}

function MetaItem({ label, value, highlight, warn }: {
  label: string; value: string; highlight?: boolean; warn?: boolean
}) {
  return (
    <div>
      <p className="text-xs text-slate-400">{label}</p>
      <p className={`text-sm font-semibold mt-0.5 ${
        highlight ? 'text-emerald-600' : warn ? 'text-amber-600' : 'text-slate-700'
      }`}>{value}</p>
    </div>
  )
}
