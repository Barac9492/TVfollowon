import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import ResearchPanel from '../detail/ResearchPanel'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface CompanyOption {
  id: string
  company_name: string
}

export default function ResearchPage() {
  const [selectedId, setSelectedId] = useState<string>('')
  const [selectedName, setSelectedName] = useState<string>('')

  const { data: companies } = useQuery<CompanyOption[]>({
    queryKey: ['company-list-simple'],
    queryFn: async () => {
      const res = await fetch(`${API}/api/companies?per_page=200`)
      if (!res.ok) throw new Error('Failed to fetch companies')
      const data = await res.json()
      return data.items.map((c: { id: string; company_name: string }) => ({
        id: c.id,
        company_name: c.company_name,
      }))
    },
  })

  const handleSelect = (id: string) => {
    setSelectedId(id)
    const company = companies?.find((c) => c.id === id)
    setSelectedName(company?.company_name || '')
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold text-slate-900 mb-1">🔍 AI 리서치</h2>
        <p className="text-sm text-slate-500">
          회사를 선택하고 텍스트 분석 또는 웹 리서치를 수행하세요
        </p>
      </div>

      <div className="max-w-2xl">
        <div className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
          <label className="block text-sm font-medium text-slate-700 mb-2">
            회사 선택
          </label>
          <select
            value={selectedId}
            onChange={(e) => handleSelect(e.target.value)}
            className="w-full text-sm border border-slate-200 rounded-lg p-3 focus:outline-none focus:border-slate-400 bg-white"
          >
            <option value="">-- 회사를 선택하세요 --</option>
            {companies?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.company_name} ({c.id})
              </option>
            ))}
          </select>
        </div>

        {selectedId && selectedName && (
          <ResearchPanel companyId={selectedId} companyName={selectedName} />
        )}
      </div>
    </div>
  )
}
