import { useState, useEffect } from 'react'

const BACKEND_URL = 'http://localhost:8000'

function App() {
  const [backendStatus, setBackendStatus] = useState('checking...')

  useEffect(() => {
    fetch(`${BACKEND_URL}/health`)
      .then((res) => res.json())
      .then((data) => setBackendStatus(data.status === 'ok' ? 'connected' : 'unexpected response'))
      .catch(() => setBackendStatus('unreachable — start the backend'))
  }, [])

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: 640, margin: '80px auto', padding: '0 24px' }}>
      <h1>JobFit</h1>
      <p>Local job application automation — placeholder dashboard.</p>

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

export default App
