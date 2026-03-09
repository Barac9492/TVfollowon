import { useMemo } from 'react'
import type { ScoreHistoryEntry, ScoreChangeReason } from '../../types'

interface Props {
  history: ScoreHistoryEntry[]
  companyName: string
}

function parseChangeReasons(json: string | null): ScoreChangeReason[] {
  if (!json) return []
  try {
    return JSON.parse(json)
  } catch {
    return []
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleDateString('ko-KR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatDateFull(dateStr: string | null): string {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

const SCORE_COLORS = {
  green: { bg: 'bg-emerald-500', text: 'text-emerald-700', label: '검토' },
  yellow: { bg: 'bg-amber-400', text: 'text-amber-700', label: '모니터' },
  red: { bg: 'bg-red-400', text: 'text-red-600', label: '홀드' },
}

const TRIGGER_LABELS: Record<string, string> = {
  auto_research: '🔍 자동 리서치',
  research_approve: '✅ 리서치 승인',
  upload: '📁 데이터 업로드',
  data_clear: '🗑 데이터 삭제',
  manual: '✏️ 수동 수정',
  initial: '🆕 초기 설정',
  unknown: '📊 점수 업데이트',
}

export default function ScoreHistoryPanel({ history }: Props) {
  // Reverse chronological display (newest first) but chart needs chronological
  const chronological = useMemo(
    () => [...history].reverse(),
    [history],
  )

  if (history.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <h3 className="font-semibold text-slate-900 mb-2">📈 점수 히스토리</h3>
        <p className="text-sm text-slate-400">아직 점수 변동 기록이 없습니다.</p>
      </div>
    )
  }

  const latest = history[0]
  const maxScore = 100

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-slate-900">📈 점수 히스토리</h3>
        <div className="flex items-center gap-2">
          <span className={`text-2xl font-bold ${SCORE_COLORS[latest.traffic_score]?.text || 'text-slate-700'}`}>
            {latest.score_value}
          </span>
          <span className="text-xs text-slate-400">/ {maxScore}</span>
          {latest.score_change !== 0 && (
            <span className={`text-sm font-medium ${latest.score_change > 0 ? 'text-emerald-600' : 'text-red-500'}`}>
              {latest.score_change > 0 ? '▲' : '▼'} {Math.abs(latest.score_change)}
            </span>
          )}
        </div>
      </div>

      {/* Mini score chart */}
      {chronological.length > 1 && (
        <MiniScoreChart entries={chronological} />
      )}

      {/* Timeline */}
      <div className="mt-4 space-y-0">
        {history.map((entry, idx) => (
          <ScoreEntry key={entry.id} entry={entry} isFirst={idx === 0} isLast={idx === history.length - 1} />
        ))}
      </div>
    </div>
  )
}

function MiniScoreChart({ entries }: { entries: ScoreHistoryEntry[] }) {
  const width = 100
  const height = 40
  const padding = 2

  const values = entries.map((e) => e.score_value)
  const min = Math.min(...values) - 5
  const max = Math.max(...values) + 5
  const range = max - min || 1

  const points = entries.map((e, i) => {
    const x = padding + (i / (entries.length - 1)) * (width - 2 * padding)
    const y = height - padding - ((e.score_value - min) / range) * (height - 2 * padding)
    return `${x},${y}`
  })

  // Color zones
  const greenY = height - padding - ((55 - min) / range) * (height - 2 * padding)
  const yellowY = height - padding - ((30 - min) / range) * (height - 2 * padding)

  return (
    <div className="w-full mb-2">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-16" preserveAspectRatio="none">
        {/* Color zone backgrounds */}
        {55 > min && 55 < max && (
          <line x1={padding} y1={greenY} x2={width - padding} y2={greenY}
            stroke="#10b981" strokeWidth="0.3" strokeDasharray="2,2" opacity="0.4" />
        )}
        {30 > min && 30 < max && (
          <line x1={padding} y1={yellowY} x2={width - padding} y2={yellowY}
            stroke="#f59e0b" strokeWidth="0.3" strokeDasharray="2,2" opacity="0.4" />
        )}

        {/* Score line */}
        <polyline
          points={points.join(' ')}
          fill="none"
          stroke="#334155"
          strokeWidth="1"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Data points */}
        {entries.map((e, i) => {
          const x = padding + (i / (entries.length - 1)) * (width - 2 * padding)
          const y = height - padding - ((e.score_value - min) / range) * (height - 2 * padding)
          const color =
            e.traffic_score === 'green' ? '#10b981' :
            e.traffic_score === 'yellow' ? '#f59e0b' : '#ef4444'
          return (
            <circle key={i} cx={x} cy={y} r="1.5" fill={color} stroke="white" strokeWidth="0.5" />
          )
        })}
      </svg>
      <div className="flex justify-between text-[10px] text-slate-400 px-1">
        <span>{formatDate(entries[0]?.created_at)}</span>
        <span>{formatDate(entries[entries.length - 1]?.created_at)}</span>
      </div>
    </div>
  )
}

function ScoreEntry({ entry, isFirst, isLast }: { entry: ScoreHistoryEntry; isFirst: boolean; isLast: boolean }) {
  const reasons = parseChangeReasons(entry.change_reasons)
  const factorChanges = reasons.filter((r) => r.factor !== 'data_completeness')
  const scoreColors = SCORE_COLORS[entry.traffic_score] || SCORE_COLORS.red
  const colorChanged = entry.previous_traffic_score && entry.previous_traffic_score !== entry.traffic_score

  return (
    <div className="flex gap-3">
      {/* Timeline line */}
      <div className="flex flex-col items-center w-6 flex-shrink-0">
        <div className={`w-0.5 flex-1 ${isFirst ? 'bg-transparent' : 'bg-slate-200'}`} />
        <div className={`w-3 h-3 rounded-full border-2 flex-shrink-0 ${
          entry.score_change > 0
            ? 'border-emerald-400 bg-emerald-50'
            : entry.score_change < 0
            ? 'border-red-400 bg-red-50'
            : 'border-slate-300 bg-slate-50'
        }`} />
        <div className={`w-0.5 flex-1 ${isLast ? 'bg-transparent' : 'bg-slate-200'}`} />
      </div>

      {/* Content */}
      <div className="flex-1 pb-4 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-400">{formatDateFull(entry.created_at)}</span>
          <span className="text-xs px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">
            {TRIGGER_LABELS[entry.trigger_type || 'unknown'] || entry.trigger_type}
          </span>
        </div>

        <div className="flex items-center gap-2 mt-1">
          <span className={`text-sm font-semibold ${scoreColors.text}`}>
            {entry.score_value}점
          </span>
          {entry.score_change !== 0 && (
            <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
              entry.score_change > 0
                ? 'bg-emerald-50 text-emerald-600'
                : 'bg-red-50 text-red-500'
            }`}>
              {entry.score_change > 0 ? '+' : ''}{entry.score_change}
            </span>
          )}
          {colorChanged && (
            <span className="text-xs">
              {SCORE_COLORS[entry.previous_traffic_score as keyof typeof SCORE_COLORS]?.label || '?'}
              {' → '}
              {scoreColors.label}
            </span>
          )}
        </div>

        {/* Meta insight */}
        {entry.meta_insight && (
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
            {entry.meta_insight}
          </p>
        )}

        {/* Factor changes */}
        {factorChanges.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1.5">
            {factorChanges.map((r, i) => (
              <span
                key={i}
                className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                  r.direction === 'up'
                    ? 'bg-emerald-50 text-emerald-600'
                    : 'bg-red-50 text-red-500'
                }`}
              >
                {r.factor_label} {r.direction === 'up' ? '+' : ''}{r.delta}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
