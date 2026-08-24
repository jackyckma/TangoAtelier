import { BrowserRouter, Navigate, Route, Routes, useParams, useSearchParams } from 'react-router-dom'
import { Layout } from './components/Layout'
import { LabPage } from './pages/LabPage'
import { HomePage } from './pages/HomePage'
import { OrchestraDetailPage } from './pages/OrchestraDetailPage'
import { OrchestrasPage } from './pages/OrchestrasPage'

function GenerateRedirect() {
  const { id = '' } = useParams()
  return <Navigate to={`/lab?style=${id}`} replace />
}

function AtelierRedirect() {
  const [searchParams] = useSearchParams()
  const q = searchParams.toString()
  return <Navigate to={q ? `/lab?${q}` : '/lab'} replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="lab" element={<LabPage />} />
          <Route path="atelier" element={<AtelierRedirect />} />
          <Route path="orchestras" element={<OrchestrasPage />} />
          <Route path="orchestras/:id" element={<OrchestraDetailPage />} />
          <Route path="generate/:id" element={<GenerateRedirect />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
