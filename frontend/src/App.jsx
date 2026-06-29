import { useState, useEffect } from 'react'
import PersonaPage from './PersonaPage'
import SearchConfigPage from './SearchConfigPage.jsx'

const BACKEND_URL = 'http://localhost:8000'

function App() {
  const [backendStatus, setBackendStatus] = useState('checking...')
  const [page, setPage] = useState('dashboard')

  useEffect(() => {
    fetch(`${BACKEND_URL}/health`)
      .then((res) => res.json())
      .then((data) => setBackendStatus(data.status === 'ok' ? 'connected' : 'unexpected response'))
      .catch(() => setBackendStatus('unreachable — start the backend'))
  }, [])

  const navStyle = {
    display: 'flex',
    gap: 12,
    borderBottom: '1px solid #e5e7eb',
    marginBottom: 32,
    paddingBottom: 8,
  }

  function navBtn(id, label) {
    return (
      <button
        key={id}
        onClick={() => setPage(id)}
        style={{
          background: 'none',
          border: 'none',
          padding: '4px 8px',
          cursor: 'pointer',
          fontWeight: page === id ? 700 : 400,
          borderBottom: page === id ? '2px solid #2563eb' : '2px solid transparent',
          color: page === id ? '#2563eb' : '#374151',
          fontSize: 14,
        }}
      >
        {label}
      </button>
    )
  }

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: 640, margin: '48px auto', padding: '0 24px' }}>
      <h1 style={{ marginBottom: 8 }}>JobFit</h1>
      <p style={{ color: '#6b7280', marginBottom: 24 }}>Local job application automation.</p>

      <nav style={navStyle}>
        {navBtn('dashboard', 'Dashboard')}
        {navBtn('search-config', 'Search Config')}
        {navBtn('persona', 'Persona')}
      </nav>

      {page === 'dashboard' && (
        <>
          <section style={{ marginBottom: 32 }}>
            <h2>Backend status</h2>
            <p>
              <code>{BACKEND_URL}/health</code> &rarr;{' '}
              <strong>{backendStatus}</strong>
            </p>
          </section>

          <section>
            <h2>Run Search</h2>
            <p>Pipeline not yet implemented. This button will trigger the full job-search pipeline.</p>
            <button disabled style={{ padding: '8px 16px', cursor: 'not-allowed', opacity: 0.5 }}>
              Run Search
            </button>
          </section>
        </>
      )}

      {page === 'search-config' && <SearchConfigPage />}
      {page === 'persona' && <PersonaPage />}
    </div>
  )
}

export default App
