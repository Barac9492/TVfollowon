const config = {
  green: { bg: 'bg-emerald-500', label: '검토', ring: 'ring-emerald-200' },
  yellow: { bg: 'bg-amber-400', label: '모니터', ring: 'ring-amber-200' },
  red: { bg: 'bg-red-400', label: '보류', ring: 'ring-red-200' },
}

export default function TrafficBadge({ score, size = 'sm' }: { score: string; size?: 'sm' | 'lg' }) {
  const c = config[score as keyof typeof config] || config.red
  const sizeClass = size === 'lg' ? 'w-4 h-4' : 'w-3 h-3'

  return (
    <div className="flex items-center gap-1.5">
      <span className={`${sizeClass} rounded-full ${c.bg} ring-2 ${c.ring}`} />
      <span className="text-xs text-slate-500 font-medium">{c.label}</span>
    </div>
  )
}
