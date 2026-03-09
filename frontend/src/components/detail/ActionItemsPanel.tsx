import type { ActionItem } from '../../types'

const priorityConfig = {
  high:   { bg: 'bg-red-50',   text: 'text-red-700',   badge: 'bg-red-100 text-red-600',   label: '높음' },
  medium: { bg: 'bg-amber-50', text: 'text-amber-700', badge: 'bg-amber-100 text-amber-600', label: '중간' },
  low:    { bg: 'bg-slate-50', text: 'text-slate-600', badge: 'bg-slate-100 text-slate-500', label: '낮음' },
}

function ActionRow({ item }: { item: ActionItem }) {
  const cfg = priorityConfig[item.priority] || priorityConfig.low
  const icon = item.type === 'missing_data' ? '📋' : item.type === 'opportunity' ? '💡' : '📈'

  return (
    <div className={`${cfg.bg} rounded-lg p-3 flex items-start justify-between gap-2`}>
      <div className="flex items-start gap-2 min-w-0">
        <span className="text-sm mt-0.5 flex-shrink-0">{icon}</span>
        <div className="min-w-0">
          <p className={`text-sm font-medium ${cfg.text}`}>{item.label}</p>
          {item.detail && (
            <p className="text-xs text-slate-400 mt-0.5">{item.detail}</p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className="text-xs font-bold text-slate-500">+{item.potential_points}점</span>
        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${cfg.badge}`}>{cfg.label}</span>
      </div>
    </div>
  )
}

export default function ActionItemsPanel({ items }: { items: ActionItem[] }) {
  if (!items || items.length === 0) return null

  const missingData = items.filter(i => i.type === 'missing_data')
  const improvements = items.filter(i => i.type !== 'missing_data')

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-slate-900">📌 개선 포인트</h3>
        <span className="text-xs text-slate-400">{items.length}개 항목</span>
      </div>

      {missingData.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">누락 데이터</p>
          <div className="space-y-2">
            {missingData.map((item, i) => (
              <ActionRow key={`m-${i}`} item={item} />
            ))}
          </div>
        </div>
      )}

      {improvements.length > 0 && (
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">점수 개선 기회</p>
          <div className="space-y-2">
            {improvements.map((item, i) => (
              <ActionRow key={`i-${i}`} item={item} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
