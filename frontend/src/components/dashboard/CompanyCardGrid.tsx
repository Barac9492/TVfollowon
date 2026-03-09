import CompanyCard from './CompanyCard'
import type { Company } from '../../types'

export default function CompanyCardGrid({ companies }: { companies: Company[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {companies.map((company) => (
        <CompanyCard key={company.id} company={company} />
      ))}
    </div>
  )
}
