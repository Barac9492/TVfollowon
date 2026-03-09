import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import type { MetricSnapshot } from '../../types'

interface Props {
  snapshots: MetricSnapshot[]
  currency: string
}

export default function MetricChart({ snapshots, currency }: Props) {
  if (snapshots.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <h3 className="font-semibold text-slate-900 mb-4">밸류에이션 추이</h3>
        <div className="flex items-center justify-center h-40 text-slate-400 text-sm">
          업로드 이력이 없습니다
        </div>
      </div>
    )
  }

  const data = snapshots.map((s) => ({
    date: s.snapshot_date ? new Date(s.snapshot_date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }) : '-',
    valuation: s.valuation || 0,
    stage: s.stage,
  }))

  const unit = currency === 'KRW' ? '억원' : 'M USD'

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <h3 className="font-semibold text-slate-900 mb-4">밸류에이션 추이</h3>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" />
          <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
          <Tooltip
            formatter={(value: number) => [`${value} ${unit}`, '밸류에이션']}
            contentStyle={{ fontSize: 12, borderRadius: 8 }}
          />
          <Area
            type="monotone"
            dataKey="valuation"
            stroke="#475569"
            fill="#e2e8f0"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
