import type { CompanyFilters } from '../../types'

interface Props {
  filters: CompanyFilters
  setFilter: (key: string, value: string | undefined) => void
}

const stages = [
  { value: '', label: '전체 단계' },
  { value: 'pre-seed', label: 'Pre-Seed' },
  { value: 'seed', label: 'Seed' },
  { value: 'pre-a', label: 'Pre-A' },
  { value: 'a', label: 'Series A' },
  { value: 'none', label: '미분류' },
]

const statuses = [
  { value: '', label: '전체 상태' },
  { value: '트래킹', label: '트래킹' },
  { value: '최종탈락', label: '최종탈락' },
]

const sortOptions = [
  { value: 'score_value', label: '스코어순' },
  { value: 'current_valuation', label: '밸류에이션순' },
  { value: 'company_name', label: '이름순' },
  { value: 'batch', label: '배치순' },
  { value: 'growth_data_completeness', label: '데이터 완성도순' },
]

const growthDataOptions = [
  { value: '', label: '성장 데이터' },
  { value: '1', label: '데이터 있음' },
  { value: '0', label: '데이터 없음' },
]

export default function FilterBar({ filters, setFilter }: Props) {
  return (
    <div className="flex flex-wrap items-center gap-3 mb-6">
      <div className="relative flex-1 min-w-[200px]">
        <input
          type="text"
          placeholder="회사명 또는 대표자 검색..."
          value={filters.search || ''}
          onChange={(e) => setFilter('search', e.target.value || undefined)}
          className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-300"
        />
        <span className="absolute left-3 top-2.5 text-slate-400 text-sm">🔍</span>
      </div>

      <select
        value={filters.stage || ''}
        onChange={(e) => setFilter('stage', e.target.value || undefined)}
        className="px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-300"
      >
        {stages.map((s) => (
          <option key={s.value} value={s.value}>{s.label}</option>
        ))}
      </select>

      <select
        value={filters.status || ''}
        onChange={(e) => setFilter('status', e.target.value || undefined)}
        className="px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-300"
      >
        {statuses.map((s) => (
          <option key={s.value} value={s.value}>{s.label}</option>
        ))}
      </select>

      <select
        value={filters.has_growth_data || ''}
        onChange={(e) => setFilter('has_growth_data', e.target.value || undefined)}
        className="px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-300"
      >
        {growthDataOptions.map((s) => (
          <option key={s.value} value={s.value}>{s.label}</option>
        ))}
      </select>

      <select
        value={filters.sort_by || 'score_value'}
        onChange={(e) => setFilter('sort_by', e.target.value)}
        className="px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-300"
      >
        {sortOptions.map((s) => (
          <option key={s.value} value={s.value}>{s.label}</option>
        ))}
      </select>

      <button
        onClick={() => setFilter('sort_dir', filters.sort_dir === 'asc' ? 'desc' : 'asc')}
        className="px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white hover:bg-slate-50"
      >
        {filters.sort_dir === 'asc' ? '↑' : '↓'}
      </button>
    </div>
  )
}
