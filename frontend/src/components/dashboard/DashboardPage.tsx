import StatsBar from './StatsBar'
import FilterBar from './FilterBar'
import CompanyCardGrid from './CompanyCardGrid'
import BulkResearchButton from './BulkResearchButton'
import { useCompanies, useDashboardStats } from '../../hooks/useCompanies'

export default function DashboardPage() {
  const { data: stats } = useDashboardStats()
  const { data, isLoading, filters, setFilter } = useCompanies()

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">포트폴리오 대시보드</h2>
          <p className="text-sm text-slate-500 mt-1">후속 투자 후보를 한눈에 확인하세요</p>
        </div>
        {data?.items && data.items.length > 0 && (
          <BulkResearchButton companies={data.items} />
        )}
      </div>

      {stats && <StatsBar stats={stats} onScoreClick={(score) => setFilter('score', filters.score === score ? undefined : score)} activeScore={filters.score} />}

      <FilterBar filters={filters} setFilter={setFilter} />

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900" />
        </div>
      ) : data?.items.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-slate-500 text-lg">데이터가 없습니다</p>
          <p className="text-slate-400 text-sm mt-2">Upload 페이지에서 엑셀 파일을 업로드하세요</p>
        </div>
      ) : (
        <CompanyCardGrid companies={data?.items || []} />
      )}

      {data && data.total > data.per_page && (
        <div className="flex justify-center gap-2 mt-6">
          {Array.from({ length: Math.ceil(data.total / data.per_page) }, (_, i) => (
            <button
              key={i}
              onClick={() => setFilter('page', String(i + 1))}
              className={`px-3 py-1 rounded text-sm ${
                data.page === i + 1
                  ? 'bg-slate-900 text-white'
                  : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              {i + 1}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
