import { useState } from 'react'
import { useUploadPortfolio, useUploadComments, useUploadGrowthData, useUploadHistory } from '../../hooks/useUpload'
import { downloadGrowthTemplate, downloadGrowthTemplatePrefilled } from '../../api/upload'
import type { UploadResponse } from '../../types'

export default function UploadPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-slate-900 mb-1">데이터 업로드</h2>
      <p className="text-sm text-slate-500 mb-6">엑셀 파일을 업로드하여 포트폴리오 데이터를 갱신합니다</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <UploadZone
          title="포트폴리오 데이터"
          description="회사 정보, 밸류에이션, 투자 단계 등"
          accept=".xlsx"
          type="portfolio"
        />
        <UploadZone
          title="투자 코멘트"
          description="회사별 투자 검토 의견"
          accept=".xlsx"
          type="comments"
        />
        <UploadZone
          title="성장 데이터"
          description="MRR, 번레이트, 런웨이, 고객수 등 성장 지표"
          accept=".xlsx"
          type="growth"
        />
      </div>

      <GrowthTemplateDownload />
      <UploadHistory />
    </div>
  )
}

function GrowthTemplateDownload() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 mb-8">
      <h3 className="font-semibold text-slate-900 mb-2">성장 데이터 템플릿</h3>
      <p className="text-xs text-slate-400 mb-4">
        성장 지표를 입력할 엑셀 템플릿을 다운로드하세요. 기존 회사 ID가 포함된 버전도 제공됩니다.
      </p>
      <div className="flex gap-3">
        <button
          onClick={() => downloadGrowthTemplate()}
          className="px-4 py-2 bg-slate-100 text-slate-700 text-sm rounded-lg hover:bg-slate-200 transition-colors"
        >
          빈 템플릿 다운로드
        </button>
        <button
          onClick={() => downloadGrowthTemplatePrefilled()}
          className="px-4 py-2 bg-slate-900 text-white text-sm rounded-lg hover:bg-slate-800 transition-colors"
        >
          회사 ID 포함 템플릿 다운로드
        </button>
      </div>
    </div>
  )
}

function UploadZone({ title, description, accept, type }: {
  title: string; description: string; accept: string; type: 'portfolio' | 'comments' | 'growth'
}) {
  const portfolioMutation = useUploadPortfolio()
  const commentsMutation = useUploadComments()
  const growthMutation = useUploadGrowthData()

  const mutation = type === 'portfolio' ? portfolioMutation : type === 'comments' ? commentsMutation : growthMutation
  const [result, setResult] = useState<UploadResponse | null>(null)
  const [dragOver, setDragOver] = useState(false)

  const handleFile = async (file: File) => {
    setResult(null)
    const res = await mutation.mutateAsync(file)
    setResult(res)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <h3 className="font-semibold text-slate-900 mb-1">{title}</h3>
      <p className="text-xs text-slate-400 mb-4">{description}</p>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragOver ? 'border-blue-400 bg-blue-50' : 'border-slate-200'
        }`}
      >
        <p className="text-3xl mb-2">{type === 'growth' ? '📈' : '📄'}</p>
        <p className="text-sm text-slate-500 mb-3">파일을 드래그하거나 선택하세요</p>
        <label className="inline-block px-4 py-2 bg-slate-900 text-white text-sm rounded-lg cursor-pointer hover:bg-slate-800">
          파일 선택
          <input
            type="file"
            accept={accept}
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) handleFile(file)
            }}
          />
        </label>
      </div>

      {mutation.isPending && (
        <div className="mt-3 flex items-center gap-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-slate-900" />
          <span className="text-sm text-slate-500">업로드 중...</span>
        </div>
      )}

      {result && (
        <div className="mt-3 bg-emerald-50 border border-emerald-200 rounded-lg p-3">
          <p className="text-sm font-medium text-emerald-700">업로드 완료</p>
          <p className="text-xs text-emerald-600 mt-1">
            파싱: {result.rows_parsed}행 | 생성: {result.rows_created} | 업데이트: {result.rows_updated}
          </p>
          {result.errors.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-amber-600 font-medium">경고 ({result.errors.length}건):</p>
              {result.errors.slice(0, 5).map((err, i) => (
                <p key={i} className="text-xs text-amber-500">{err}</p>
              ))}
            </div>
          )}
        </div>
      )}

      {mutation.isError && (
        <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm text-red-700">업로드 실패: {(mutation.error as Error).message}</p>
        </div>
      )}
    </div>
  )
}

function UploadHistory() {
  const { data: history } = useUploadHistory()

  if (!history || history.length === 0) return null

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <h3 className="font-semibold text-slate-900 mb-4">업로드 이력</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-400 text-xs">
            <th className="pb-2">파일명</th>
            <th className="pb-2">유형</th>
            <th className="pb-2">파싱</th>
            <th className="pb-2">생성</th>
            <th className="pb-2">업데이트</th>
            <th className="pb-2">일시</th>
          </tr>
        </thead>
        <tbody>
          {history.map((h) => (
            <tr key={h.id} className="border-t border-slate-100">
              <td className="py-2 text-slate-700">{h.filename}</td>
              <td className="py-2 text-slate-500">{h.file_type}</td>
              <td className="py-2 text-slate-500">{h.rows_parsed}</td>
              <td className="py-2 text-slate-500">{h.rows_created}</td>
              <td className="py-2 text-slate-500">{h.rows_updated}</td>
              <td className="py-2 text-slate-400">
                {h.uploaded_at ? new Date(h.uploaded_at).toLocaleString('ko-KR') : '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
