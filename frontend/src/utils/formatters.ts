export function formatValuation(value: number | null, currency: string): string {
  if (value === null || value === undefined) return '-'
  if (currency === 'KRW') {
    return `${value}억원`
  }
  return `$${value}M`
}

export function formatUSD(value: number | null): string {
  if (value === null || value === undefined) return '-'
  if (value >= 1) return `$${value.toFixed(1)}M`
  return `$${(value * 1000).toFixed(0)}K`
}

export function stageLabel(stage: string | null): string {
  const labels: Record<string, string> = {
    'pre-seed': 'Pre-Seed',
    'seed': 'Seed',
    'pre-a': 'Pre-A',
    'a': 'Series A',
    'none': '-',
  }
  return labels[stage || 'none'] || stage || '-'
}

export function scoreLabel(score: string): string {
  const labels: Record<string, string> = {
    green: '검토 필요',
    yellow: '모니터링',
    red: '보류',
  }
  return labels[score] || score
}

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('ko-KR')
}

export function formatGrowthRate(pct: number | null): string {
  if (pct === null || pct === undefined) return '-'
  const sign = pct >= 0 ? '+' : ''
  return `${sign}${pct.toFixed(1)}%`
}

export function formatRunway(months: number | null): string {
  if (months === null || months === undefined) return '-'
  return `${months.toFixed(0)}개월`
}

export function formatRevenue(value: number | null, currency?: string): string {
  if (value === null || value === undefined) return '-'
  if (currency === 'USD' || (!currency && value < 1000)) {
    if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
    if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
    return `$${value.toFixed(0)}`
  }
  if (value >= 100_000_000) return `${(value / 100_000_000).toFixed(1)}억`
  if (value >= 10_000) return `${(value / 10_000).toFixed(0)}만`
  return `${value.toLocaleString()}`
}
