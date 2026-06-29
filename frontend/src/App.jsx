import { useState, useEffect } from 'react'
import PersonaPage from './PersonaPage'

const BACKEND_URL = 'http://localhost:8000'

function HomePage() {
  const [backendStatus, setBackendStatus] = useState('checking...')

  useEffect(() => {
    fetch(`${BACKEND_URL}/health`)
      .then((res) => res.json())
      .then((data) => setBackendStatus(data.status === 'ok' ? 'connected' : 'unexpected response'))
      .catch(() => setBackendStatus('unreachable — start the backend'))
  }, [])

  return (
    <div>
      <section style={{ marginTop: 32 }}>
        <h2>Backend status</h2>
        <p>
          <code>{BACKEND_URL}/health</code> &rarr;{' '}
          <strong>{backendStatus}</strong>
        </p>
      </section>

      <section style={{ marginTop: 32 }}>
        <h2>Run Search</h2>
        <p>Pipeline not yet implemented. This button will trigger the full job-search pipeline.</p>
        <button disabled style={{ padding: '8px 16px', cursor: 'not-allowed', opacity: 0.5 }}>
          Run Search
        </button>
      </section>
    </div>
  )
}

function App() {
  const [page, setPage] = useState('home')

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: 640, margin: '80px auto', padding: '0 24px' }}>
      <h1>JobFit</h1>
      <p>Local job application automation — placeholder dashboard.</p>

      <nav style={{ marginTop: 16, display: 'flex', gap: 16 }}>
        <button
          onClick={() => setPage('home')}
          style={navBtnStyle(page === 'home')}
        >
          Home
        </button>
        <button
          onClick={() => setPage('persona')}
          style={navBtnStyle(page === 'persona')}
        >
          Persona
        </button>
      </nav>

      <div style={{ marginTop: 24 }}>
        {page === 'home' && <HomePage />}
        {page === 'persona' && <PersonaPage />}
      </div>
    </div>
  )
}

function navBtnStyle(active) {
  return {
    padding: '6px 14px',
    cursor: 'pointer',
    background: active ? '#0070f3' : '#eee',
    color: active ? '#fff' : '#333',
    border: 'none',
    borderRadius: 4,
    fontWeight: active ? 600 : 400,
  }
}

export default App
