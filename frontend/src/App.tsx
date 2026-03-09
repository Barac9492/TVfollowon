import { Routes, Route } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import DashboardPage from './components/dashboard/DashboardPage'
import CompanyDetailPage from './components/detail/CompanyDetailPage'
import UploadPage from './components/upload/UploadPage'
import SettingsPage from './components/settings/SettingsPage'
import ResearchPage from './components/research/ResearchPage'

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/company/:id" element={<CompanyDetailPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/research" element={<ResearchPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </AppShell>
  )
}
