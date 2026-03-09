import { useQuery } from '@tanstack/react-query'
import { fetchSlackStatus, fetchSlackMessages, fetchSlackSummary } from '../../api/slack'

interface Props {
  companyId: string
  companyName: string
}

export default function SlackPanel({ companyId, companyName }: Props) {
  const { data: status } = useQuery({
    queryKey: ['slack-status'],
    queryFn: fetchSlackStatus,
  })

  const { data: messages } = useQuery({
    queryKey: ['slack-messages', companyId],
    queryFn: () => fetchSlackMessages(companyId),
    enabled: status?.connected === true,
  })

  const { data: summary } = useQuery({
    queryKey: ['slack-summary', companyId],
    queryFn: () => fetchSlackSummary(companyId),
    enabled: status?.connected === true,
  })

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <h3 className="font-semibold text-slate-900 mb-4">Slack 커뮤니케이션</h3>

      {!status?.connected ? (
        <div className="text-center py-8">
          <p className="text-4xl mb-3">💬</p>
          <p className="text-sm text-slate-500">Slack이 연결되어 있지 않습니다</p>
          <p className="text-xs text-slate-400 mt-1">
            Settings 페이지에서 Slack을 연결하세요
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {summary && (
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
              <p className="text-xs text-blue-600 font-medium mb-1">AI 요약</p>
              <p className="text-sm text-blue-900">{summary.summary_text}</p>
              {summary.message_count && (
                <p className="text-xs text-blue-400 mt-2">
                  {summary.message_count}개 메시지 기반
                </p>
              )}
            </div>
          )}

          {messages && messages.length > 0 ? (
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {messages.map((m, i) => (
                <div key={i} className="border border-slate-100 rounded p-2">
                  <p className="text-xs text-slate-400 font-medium">{m.user_name}</p>
                  <p className="text-sm text-slate-700 mt-0.5">{m.text}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-400">
              {companyName}에 매핑된 Slack 채널이 없습니다.
              Settings에서 채널을 매핑하세요.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
