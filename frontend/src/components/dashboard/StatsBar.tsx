import type { DashboardStats } from '../../types'
import { formatUSD } from '../../utils/formatters'

interface Props {
  stats: DashboardStats
  onScoreClick: (score: string) => void
  activeScore?: string
}

export default function StatsBar({ stats, onScoreClick, activeScore }: Props) {
  const cards = [
    { label: '전체', value: stats.total_companies, color: 'bg-slate-100 text-slate-900', key: '' },
    { label: '검토 필요', value: stats.green_count, color: 'bg-emerald-50 text-emerald-700 border-emerald-200', key: 'green' },
    { label: '모니터링', value: stats.yellow_count, color: 'bg-amber-50 text-amber-700 border-amber-200', key: 'yellow' },
    { label: '보류', value: stats.red_count, color: 'bg-red-50 text-red-700 border-red-200', key: 'red' },
  ]

  return (
    <div className="space-y-4 mb-6">
      <div className="grid grid-cols-4 gap-4">
        {cards.map((card) => (
          <button
            key={card.label}
            onClick={() => card.key && onScoreClick(card.key)}
            className={`rounded-xl p-4 text-left border transition-all ${card.color} ${
              activeScore === card.key ? 'ring-2 ring-offset-1 ring-slate-400' : ''
            } ${card.key ? 'cursor-pointer hover:shadow-md' : 'cursor-default'}`}
          >
            <p className="text-xs font-medium opacity-70">{card.label}</p>
            <p className="text-2xl font-bold mt-1">{card.value}</p>
            {card.label === '전체' && stats.avg_valuation_usd && (
              <p className="text-xs opacity-60 mt-1">평균 {formatUSD(stats.avg_valuation_usd)}</p>
            )}
          </button>
        ))}
      </div>

      <div className="flex items-center gap-4 px-1 text-xs text-slate-500">
        <span>성장 데이터: <strong className="text-slate-700">{stats.growth_data_count}</strong>개사</span>
        {stats.avg_mrr_growth !== null && stats.avg_mrr_growth !== undefined && (
          <span>평균 MRR 성장: <strong className={stats.avg_mrr_growth >= 10 ? 'text-emerald-600' : 'text-slate-700'}>
            {stats.avg_mrr_growth >= 0 ? '+' : ''}{stats.avg_mrr_growth.toFixed(1)}%
          </strong></span>
        )}
        {stats.funding_window_count > 0 && (
          <span>펀딩 윈도우: <strong className="text-amber-600">{stats.funding_window_count}</strong>개사</span>
        )}
      </div>
    </div>
  )
}
