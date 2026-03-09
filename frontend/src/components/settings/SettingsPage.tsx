import { useQuery } from '@tanstack/react-query'
import { fetchSlackStatus } from '../../api/slack'

export default function SettingsPage() {
  const { data: slackStatus } = useQuery({
    queryKey: ['slack-status'],
    queryFn: fetchSlackStatus,
  })

  return (
    <div>
      <h2 className="text-2xl font-bold text-slate-900 mb-1">설정</h2>
      <p className="text-sm text-slate-500 mb-6">외부 서비스 연동 및 대시보드 설정</p>

      <div className="space-y-6">
        {/* Slack Integration */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-slate-900">Slack 연동</h3>
              <p className="text-xs text-slate-400 mt-0.5">포트폴리오사 채널의 대화를 가져옵니다</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
              slackStatus?.connected
                ? 'bg-emerald-50 text-emerald-700'
                : 'bg-slate-100 text-slate-500'
            }`}>
              {slackStatus?.connected ? '연결됨' : '미연결'}
            </span>
          </div>

          {slackStatus?.connected ? (
            <div className="bg-emerald-50 border border-emerald-100 rounded-lg p-3">
              <p className="text-sm text-emerald-700">
                워크스페이스: {slackStatus.workspace_name}
              </p>
            </div>
          ) : (
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <p className="text-sm text-slate-600 mb-3">
                Slack을 연동하려면 백엔드 <code className="bg-slate-200 px-1 rounded">.env</code> 파일에 다음을 추가하세요:
              </p>
              <pre className="bg-slate-800 text-slate-200 text-xs p-3 rounded-lg overflow-x-auto">
                SLACK_BOT_TOKEN=xoxb-your-token-here
              </pre>
              <p className="text-xs text-slate-400 mt-2">
                Slack App을 생성하고 Bot Token을 발급받으세요. channels:read, channels:history 권한이 필요합니다.
              </p>
            </div>
          )}
        </div>

        {/* AI Summarization */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h3 className="font-semibold text-slate-900 mb-1">AI 요약</h3>
          <p className="text-xs text-slate-400 mb-4">Claude API를 사용하여 Slack 대화를 요약합니다</p>

          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
            <p className="text-sm text-slate-600 mb-3">
              AI 요약을 활성화하려면 <code className="bg-slate-200 px-1 rounded">.env</code> 파일에 추가:
            </p>
            <pre className="bg-slate-800 text-slate-200 text-xs p-3 rounded-lg overflow-x-auto">
              CLAUDE_API_KEY=sk-ant-your-key-here
            </pre>
          </div>
        </div>
      </div>
    </div>
  )
}
