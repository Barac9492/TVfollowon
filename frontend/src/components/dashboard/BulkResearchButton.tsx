import { useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import {
  fetchResearchStatus,
  autoResearchCompany,
  clearGrowthData,
} from '../../api/research'
import type { AutoResearchResult } from '../../api/research'
import type { Company } from '../../types'

interface Props {
  companies: Company[]
}

export default function BulkResearchButton({ companies }: Props) {
  const [isOpen, setIsOpen] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState<AutoResearchResult[]>([])
  const [aiEnabled, setAiEnabled] = useState<boolean | null>(null)
  const queryClient = useQueryClient()

  const checkStatus = useCallback(async () => {
    try {
      const status = await fetchResearchStatus()
      setAiEnabled(status.enabled)
    } catch {
      setAiEnabled(false)
    }
  }, [])

  const handleOpen = async () => {
    setIsOpen(true)
    setResults([])
    setProgress(0)
    await checkStatus()
  }

  const handleClearData = async () => {
    if (!confirm('모든 성장 데이터를 삭제하시겠습니까? (샘플 데이터 포함)')) return
    try {
      const res = await clearGrowthData()
      alert(res.message)
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
    } catch (err) {
      alert(`삭제 실패: ${(err as Error).message}`)
    }
  }

  const handleRunBulk = async () => {
    setIsRunning(true)
    setProgress(0)
    setResults([])

    const total = companies.length
    const newResults: AutoResearchResult[] = []

    for (let i = 0; i < total; i++) {
      const company = companies[i]
      try {
        const result = await autoResearchCompany(company.id)
        newResults.push(result)
      } catch (err) {
        newResults.push({
          company_id: company.id,
          company_name: company.company_name,
          success: false,
          has_data: false,
          confidence: 'low',
          notes: null,
          error: (err as Error).message,
        })
      }
      setProgress(i + 1)
      setResults([...newResults])
    }

    setIsRunning(false)
    queryClient.invalidateQueries({ queryKey: ['companies'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
  }

  const dataFound = results.filter((r) => r.has_data).length
  const failed = results.filter((r) => !r.success).length

  if (!isOpen) {
    return (
      <button
        onClick={handleOpen}
        className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white text-sm rounded-lg hover:bg-slate-800 transition-colors"
      >
        🔍 전체 리서치 업데이트
      </button>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 max-h-[80vh] flex flex-col">
        <div className="p-5 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-900">🔍 전체 리서치 업데이트</h3>
            <button
              onClick={() => { setIsOpen(false); setIsRunning(false) }}
              className="text-slate-400 hover:text-slate-600"
              disabled={isRunning}
            >
              ✕
            </button>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            {companies.length}개 회사에 대해 웹 검색으로 성장 데이터를 수집합니다
          </p>
        </div>

        <div className="p-5 flex-1 overflow-y-auto">
          {aiEnabled === false && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-amber-700">
                ⚠️ CLAUDE_API_KEY가 설정되지 않았습니다. Settings에서 설정하세요.
              </p>
            </div>
          )}

          {!isRunning && results.length === 0 && (
            <div className="space-y-3">
              <button
                onClick={handleRunBulk}
                disabled={!aiEnabled}
                className="w-full bg-slate-900 text-white text-sm py-3 rounded-lg hover:bg-slate-800 disabled:opacity-50 transition-colors"
              >
                🚀 {companies.length}개 회사 리서치 시작
              </button>
              <button
                onClick={handleClearData}
                className="w-full text-sm py-2 text-red-500 hover:text-red-700 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
              >
                🗑 기존 성장 데이터 전체 삭제 (샘플 데이터 제거)
              </button>
            </div>
          )}

          {isRunning && (
            <div className="mb-4">
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-slate-600">진행 중...</span>
                <span className="text-slate-500">{progress}/{companies.length}</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-slate-900 rounded-full transition-all duration-300"
                  style={{ width: `${(progress / companies.length) * 100}%` }}
                />
              </div>
              {results.length > 0 && (
                <p className="text-xs text-slate-400 mt-2">
                  현재: {results[results.length - 1]?.company_name}
                </p>
              )}
            </div>
          )}

          {results.length > 0 && !isRunning && (
            <div className="bg-slate-50 rounded-lg p-3 mb-4">
              <p className="text-sm font-medium text-slate-700 mb-1">완료!</p>
              <div className="flex gap-4 text-xs text-slate-500">
                <span>✅ 데이터 확보: {dataFound}건</span>
                <span>📭 미확보: {results.length - dataFound - failed}건</span>
                {failed > 0 && <span>❌ 실패: {failed}건</span>}
              </div>
            </div>
          )}

          {results.length > 0 && (
            <div className="space-y-1.5 max-h-60 overflow-y-auto">
              {results.map((r) => (
                <div
                  key={r.company_id}
                  className="flex items-center justify-between text-xs bg-white rounded p-2 border border-slate-100"
                >
                  <span className="text-slate-700 truncate flex-1">{r.company_name}</span>
                  {!r.success ? (
                    <span className="text-red-500 ml-2">❌</span>
                  ) : r.has_data ? (
                    <span className="text-emerald-600 ml-2">✅ {r.confidence}</span>
                  ) : (
                    <span className="text-slate-400 ml-2">📭 없음</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="p-4 border-t border-slate-200">
          <button
            onClick={() => { setIsOpen(false); setIsRunning(false) }}
            className="w-full text-sm text-slate-500 hover:text-slate-700 py-2"
            disabled={isRunning}
          >
            {isRunning ? '리서치 진행 중...' : '닫기'}
          </button>
        </div>
      </div>
    </div>
  )
}
