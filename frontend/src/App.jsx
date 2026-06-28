import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import RunPage from './pages/RunPage.jsx'
import ResultsPage from './pages/ResultsPage.jsx'
import './App.css'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RunPage />} />
        <Route path="/results/:runId" element={<ResultsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
