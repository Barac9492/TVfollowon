import { useState } from 'react'
import type { Comment } from '../../types'
import { formatDate } from '../../utils/formatters'

export default function CommentsList({ comments }: { comments: Comment[] }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <h3 className="font-semibold text-slate-900 mb-4">
        투자 코멘트 <span className="text-slate-400 font-normal">({comments.length})</span>
      </h3>
      {comments.length === 0 ? (
        <p className="text-sm text-slate-400">코멘트가 없습니다</p>
      ) : (
        <div className="space-y-3 max-h-[500px] overflow-y-auto">
          {comments.map((comment) => (
            <CommentItem key={comment.id} comment={comment} />
          ))}
        </div>
      )}
    </div>
  )
}

function CommentItem({ comment }: { comment: Comment }) {
  const [expanded, setExpanded] = useState(false)
  const isLong = comment.comment_text.length > 200

  return (
    <div className="border border-slate-100 rounded-lg p-3">
      <div className="flex justify-between items-start mb-1">
        <span className="text-xs text-slate-400">{formatDate(comment.created_at)}</span>
      </div>
      <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
        {isLong && !expanded ? comment.comment_text.slice(0, 200) + '...' : comment.comment_text}
      </p>
      {isLong && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-blue-500 mt-1 hover:underline"
        >
          {expanded ? '접기' : '더보기'}
        </button>
      )}
    </div>
  )
}
