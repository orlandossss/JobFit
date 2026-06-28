import { BrowserRouter, Routes, Route, Navigate, NavLink } from 'react-router-dom'
import RunPage from './pages/RunPage.jsx'
import ResultsPage from './pages/ResultsPage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'
import './App.css'

export default function App() {
  return (
    <BrowserRouter>
      <nav className="app-nav">
        <NavLink to="/" end className={({ isActive }) => isActive ? 'app-nav-link app-nav-link--active' : 'app-nav-link'}>
          Home
        </NavLink>
        <NavLink to="/history" className={({ isActive }) => isActive ? 'app-nav-link app-nav-link--active' : 'app-nav-link'}>
          History
        </NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<RunPage />} />
        <Route path="/results/:runId" element={<ResultsPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
