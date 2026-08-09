import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router-dom'
import { Layout } from './components/Layout'
import { AtelierPage } from './pages/AtelierPage'
import { HomePage } from './pages/HomePage'
import { OrchestraDetailPage } from './pages/OrchestraDetailPage'
import { OrchestrasPage } from './pages/OrchestrasPage'

function GenerateRedirect() {
  const { id = '' } = useParams()
  return <Navigate to={`/atelier?style=${id}`} replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="atelier" element={<AtelierPage />} />
          <Route path="orchestras" element={<OrchestrasPage />} />
          <Route path="orchestras/:id" element={<OrchestraDetailPage />} />
          <Route path="generate/:id" element={<GenerateRedirect />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
