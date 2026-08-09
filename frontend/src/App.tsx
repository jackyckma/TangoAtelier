import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { HomePage } from './pages/HomePage'
import { OrchestraDetailPage } from './pages/OrchestraDetailPage'
import { OrchestrasPage } from './pages/OrchestrasPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="orchestras" element={<OrchestrasPage />} />
          <Route path="orchestras/:id" element={<OrchestraDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
