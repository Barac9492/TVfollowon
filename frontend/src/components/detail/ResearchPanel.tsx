import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchResearchStatus,
  extractFromText,
  webResearch,
  approveResearch,
  fetchResearchHistory,
  chatWithAgent,
} from '../../api/research'
import type { ChatMessage } from '../../api/research'
import type { ResearchResult, ResearchLogItem } from '../../types'
import { formatDate } from '../../utils/formatters'

interface Props {
  companyId: string
  companyName: string
}

type Tab = 'extract' | 'web' | 'chat' | 'history'

const METRIC_FIELDS: { key: string; label: string; type: 'number' | 'text' }[] = [
  { key: 'monthly_revenue', label: '월매출', type: 'number' },
  { key: 'mrr', label: 'MRR', type: 'number' },
  { key: 'arr', label: 'ARR', type: 'number' },
  { key: 'mrr_growth_rate_pct', label: 'MRR 성장률 (%)', type: 'number' },
  { key: 'monthly_burn', label: '월 번', type: 'number' },
  { key: 'cash_on_hand', label: '보유 현금', type: 'number' },
  { key: 'runway_months', label: '런웨이 (개월)', type: 'number' },
  { key: 'headcount', label: '인원', type: 'number' },
  { key: 'paying_customers', label: '유료 고객', type: 'number' },
  { key: 'ndr_pct', label: 'NDR (%)', type: 'number' },
  { key: 'last_funding_round', label: '최근 라운드', type: 'text' },
  { key: 'last_funding_amount', label: '펀딩 금액', type: 'number' },
  { key: 'last_funding_date', label: '펀딩 일자', type: 'text' },
  { key: 'key_metric_name', label: '핵심 KPI 이름', type: 'text' },
  { key: 'key_metric_value', label: '핵심 KPI 값', type: 'number' },
]

function confidenceBadge(c: string) {
  if (c === 'high') return <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">높음</span>
  if (c === 'medium') return <span className="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-700">보통</span>
  return <span className="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-700">낮음</span>
}

function MetricsReviewForm({
  result,
  onApprove,
  isApproving,
  onCancel,
}: {
  result: ResearchResult
  onApprove: (metrics: Record<string, unknown>) => void
  isApproving: boolean
  onCancel: () => void
}) {
  const [metrics, setMetrics] = useState<Record<string, unknown>>({ ...result.metrics })
  const [investorsText, setInvestorsText] = useState(() => {
    const inv = result.metrics.investors as { name: string; round?: string; role?: string }[] | undefined
    if (Array.isArray(inv)) {
      return inv.map((i) => `${i.name}${i.round ? ` (${i.round})` : ''}`).join(', ')
    }
    return ''
  })

  const updateField = (key: string, value: string, type: 'number' | 'text') => {
    if (type === 'number') {
      setMetrics((prev) => ({ ...prev, [key]: value === '' ? null : Number(value) }))
    } else {
      setMetrics((prev) => ({ ...prev, [key]: value || null }))
    }
  }

  const handleApprove = () => {
    // Parse investors text back to array
    const investorsList = investorsText
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)
      .map((s) => {
        const match = s.match(/^(.+?)\s*\((.+?)\)$/)
        return match
          ? { name: match[1].trim(), round: match[2].trim(), role: 'unknown' }
          : { name: s, round: '', role: 'unknown' }
      })
    onApprove({ ...metrics, investors: investorsList })
  }

  return (
    <div className="space-y-4 mt-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-700">추출된 데이터 검토</span>
        {confidenceBadge(result.confidence)}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {METRIC_FIELDS.map((f) => {
          const val = metrics[f.key]
          return (
            <div key={f.key} className="bg-slate-50 rounded-lg p-2">
              <label className="text-[10px] text-slate-400 block">{f.label}</label>
              <input
                type={f.type === 'number' ? 'number' : 'text'}
                className="w-full text-sm font-medium text-slate-700 bg-transparent border-b border-slate-200 focus:border-slate-500 outline-none py-0.5"
                value={val != null ? String(val) : ''}
                placeholder="-"
                onChange={(e) => updateField(f.key, e.target.value, f.type)}
              />
            </div>
          )
        })}
      </div>

      <div className="bg-slate-50 rounded-lg p-2">
        <label className="text-[10px] text-slate-400 block">투자자 (콤마로 구분)</label>
        <input
          type="text"
          className="w-full text-sm text-slate-700 bg-transparent border-b border-slate-200 focus:border-slate-500 outline-none py-0.5"
          value={investorsText}
          placeholder="예: Y Combinator (seed), 소프트뱅크벤처스 (series-a)"
          onChange={(e) => setInvestorsText(e.target.value)}
        />
      </div>

      {result.notes && (
        <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
          <p className="text-xs text-blue-600 font-medium mb-1">AI 분석 노트</p>
          <p className="text-sm text-blue-900">{result.notes}</p>
        </div>
      )}

      {result.sources && result.sources.length > 0 && (
        <div className="bg-slate-50 rounded-lg p-3">
          <p className="text-xs text-slate-500 font-medium mb-1">출처</p>
          <div className="space-y-1">
            {result.sources.map((s, i) => (
              <a
                key={i}
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-xs text-blue-600 hover:underline truncate"
              >
                {s.title || s.url}
              </a>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-2 pt-2">
        <button
          onClick={handleApprove}
          disabled={isApproving}
          className="flex-1 bg-slate-900 text-white text-sm py-2 rounded-lg hover:bg-slate-800 disabled:opacity-50 transition-colors"
        >
          {isApproving ? '저장 중...' : '승인 및 저장'}
        </button>
        <button
          onClick={onCancel}
          className="px-4 text-sm text-slate-500 hover:text-slate-700 transition-colors"
        >
          취소
        </button>
      </div>
    </div>
  )
}

function ChatTab({ companyId }: { companyId: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    const text = input.trim()
    if (!text || isLoading) return

    const userMsg: ChatMessage = { role: 'user', content: text }
    const updatedMessages = [...messages, userMsg]
    setMessages(updatedMessages)
    setInput('')
    setIsLoading(true)

    try {
      const { reply } = await chatWithAgent(companyId, text, messages)
      setMessages([...updatedMessages, { role: 'assistant', content: reply }])
    } catch (err) {
      setMessages([
        ...updatedMessages,
        { role: 'assistant', content: `오류가 발생했습니다: ${(err as Error).message}` },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col mt-2" style={{ height: '400px' }}>
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-3 mb-3 pr-1"
      >
        {messages.length === 0 && (
          <div className="text-center py-8">
            <p className="text-2xl mb-2">💬</p>
            <p className="text-sm text-slate-500">성장 데이터 분석에 대해 질문하세요</p>
            <div className="mt-3 space-y-1">
              {[
                '이 회사의 성장률을 추정하려면 어떤 데이터를 봐야 할까요?',
                '웹에서 직접 매출을 찾을 수 없는 경우 proxy metric은?',
                '이 단계에서 적절한 밸류에이션 레인지는?',
              ].map((hint, i) => (
                <button
                  key={i}
                  onClick={() => setInput(hint)}
                  className="block w-full text-left text-xs text-blue-600 hover:text-blue-800 bg-blue-50 rounded-lg px-3 py-1.5 transition-colors"
                >
                  {hint}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'bg-slate-900 text-white'
                  : 'bg-slate-100 text-slate-800'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 rounded-lg px-3 py-2">
              <span className="flex items-center gap-2 text-sm text-slate-500">
                <span className="animate-spin h-3 w-3 border-2 border-slate-400 border-t-transparent rounded-full" />
                생각 중...
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          className="flex-1 text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:border-slate-400"
          placeholder="질문을 입력하세요..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          disabled={isLoading}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          className="px-4 bg-slate-900 text-white text-sm rounded-lg hover:bg-slate-800 disabled:opacity-50 transition-colors"
        >
          전송
        </button>
      </div>
    </div>
  )
}

function HistoryTab({ companyId }: { companyId: string }) {
  const { data: logs } = useQuery({
    queryKey: ['research-history', companyId],
    queryFn: () => fetchResearchHistory(companyId),
  })

  if (!logs || logs.length === 0) {
    return <p className="text-sm text-slate-400 text-center py-4">리서치 이력이 없습니다</p>
  }

  return (
    <div className="space-y-2 mt-3">
      {logs.map((log: ResearchLogItem) => (
        <div key={log.id} className="bg-slate-50 rounded-lg p-3 flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-600">
              {log.research_type === 'text_extraction' ? '📋 텍스트 분석' : '🔍 웹 리서치'}
            </span>
            {log.created_at && (
              <span className="text-xs text-slate-400 ml-2">{formatDate(log.created_at)}</span>
            )}
          </div>
          <span
            className={`text-xs px-2 py-0.5 rounded-full ${
              log.status === 'approved'
                ? 'bg-emerald-50 text-emerald-700'
                : log.status === 'rejected'
                  ? 'bg-red-50 text-red-700'
                  : 'bg-amber-50 text-amber-700'
            }`}
          >
            {log.status === 'approved' ? '승인됨' : log.status === 'rejected' ? '거절됨' : '대기중'}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function ResearchPanel({ companyId, companyName }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('extract')
  const [inputText, setInputText] = useState('')
  const [webContext, setWebContext] = useState('')
  const [result, setResult] = useState<ResearchResult | null>(null)
  const queryClient = useQueryClient()

  const { data: status } = useQuery({
    queryKey: ['research-status'],
    queryFn: fetchResearchStatus,
  })

  const extractMutation = useMutation({
    mutationFn: () => extractFromText(companyId, companyName, inputText),
    onSuccess: (data) => setResult(data),
  })

  const webMutation = useMutation({
    mutationFn: () => webResearch(companyId, companyName, webContext),
    onSuccess: (data) => setResult(data),
  })

  const approveMutation = useMutation({
    mutationFn: (metrics: Record<string, unknown>) =>
      approveResearch(result!.research_id, metrics),
    onSuccess: () => {
      setResult(null)
      setInputText('')
      setWebContext('')
      queryClient.invalidateQueries({ queryKey: ['company', companyId] })
      queryClient.invalidateQueries({ queryKey: ['research-history', companyId] })
      queryClient.invalidateQueries({ queryKey: ['companies'] })
    },
  })

  const tabs: { key: Tab; label: string }[] = [
    { key: 'extract', label: '📋 텍스트 분석' },
    { key: 'web', label: '🔍 웹 리서치' },
    { key: 'chat', label: '💬 상담' },
    { key: 'history', label: '📜 이력' },
  ]

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <h3 className="font-semibold text-slate-900 mb-4">🤖 AI 리서치</h3>

      {!status?.enabled ? (
        <div className="text-center py-6">
          <p className="text-3xl mb-2">🔑</p>
          <p className="text-sm text-slate-500">AI 리서치를 사용하려면</p>
          <p className="text-xs text-slate-400 mt-1">
            Settings에서 Claude API 키를 설정하세요
          </p>
        </div>
      ) : (
        <>
          <div className="flex gap-1 bg-slate-100 rounded-lg p-0.5 mb-4">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => {
                  setActiveTab(tab.key)
                  setResult(null)
                }}
                className={`flex-1 text-xs py-1.5 rounded-md transition-colors ${
                  activeTab === tab.key
                    ? 'bg-white text-slate-900 font-medium shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {activeTab === 'extract' && (
            <div>
              {!result ? (
                <div className="space-y-3">
                  <textarea
                    className="w-full h-32 text-sm border border-slate-200 rounded-lg p-3 resize-none focus:outline-none focus:border-slate-400"
                    placeholder="파운더 이메일, 리포트, 기사 등 텍스트를 붙여넣으세요..."
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                  />
                  <button
                    onClick={() => extractMutation.mutate()}
                    disabled={!inputText.trim() || extractMutation.isPending}
                    className="w-full bg-slate-900 text-white text-sm py-2 rounded-lg hover:bg-slate-800 disabled:opacity-50 transition-colors"
                  >
                    {extractMutation.isPending ? (
                      <span className="flex items-center justify-center gap-2">
                        <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                        분석 중...
                      </span>
                    ) : (
                      '분석하기'
                    )}
                  </button>
                  {extractMutation.isError && (
                    <p className="text-xs text-red-500">{(extractMutation.error as Error).message}</p>
                  )}
                </div>
              ) : (
                <MetricsReviewForm
                  result={result}
                  onApprove={(m) => approveMutation.mutate(m)}
                  isApproving={approveMutation.isPending}
                  onCancel={() => setResult(null)}
                />
              )}
              {approveMutation.isSuccess && (
                <p className="text-sm text-emerald-600 text-center mt-3">
                  ✅ 성장 데이터가 저장되었습니다!
                </p>
              )}
            </div>
          )}

          {activeTab === 'web' && (
            <div>
              {!result ? (
                <div className="space-y-3">
                  <input
                    type="text"
                    className="w-full text-sm border border-slate-200 rounded-lg p-3 focus:outline-none focus:border-slate-400"
                    placeholder="추가 컨텍스트 (선택): 업종, 투자 단계, 특이사항 등"
                    value={webContext}
                    onChange={(e) => setWebContext(e.target.value)}
                  />
                  <button
                    onClick={() => webMutation.mutate()}
                    disabled={webMutation.isPending}
                    className="w-full bg-slate-900 text-white text-sm py-2 rounded-lg hover:bg-slate-800 disabled:opacity-50 transition-colors"
                  >
                    {webMutation.isPending ? (
                      <span className="flex items-center justify-center gap-2">
                        <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                        웹 검색 중... (최대 30초)
                      </span>
                    ) : (
                      `🔍 ${companyName} 리서치 시작`
                    )}
                  </button>
                  {webMutation.isError && (
                    <p className="text-xs text-red-500">{(webMutation.error as Error).message}</p>
                  )}
                </div>
              ) : (
                <MetricsReviewForm
                  result={result}
                  onApprove={(m) => approveMutation.mutate(m)}
                  isApproving={approveMutation.isPending}
                  onCancel={() => setResult(null)}
                />
              )}
              {approveMutation.isSuccess && (
                <p className="text-sm text-emerald-600 text-center mt-3">
                  ✅ 성장 데이터가 저장되었습니다!
                </p>
              )}
            </div>
          )}

          {activeTab === 'chat' && <ChatTab companyId={companyId} />}

          {activeTab === 'history' && <HistoryTab companyId={companyId} />}
        </>
      )}
    </div>
  )
}
