import { useState, useEffect, useRef } from 'react'
import SearchConfigPage from './SearchConfigPage.jsx'

const BACKEND_URL = 'http://localhost:8000'

const PAGES = ['dashboard', 'search-config']

function App() {
  const [backendStatus, setBackendStatus] = useState('checking...')
  const [page, setPage] = useState('dashboard')
  const [running, setRunning] = useState(false)
  const [progressLog, setProgressLog] = useState([])
  const logEndRef = useRef(null)

  useEffect(() => {
    fetch(`${BACKEND_URL}/health`)
      .then((res) => res.json())
      .then((data) => setBackendStatus(data.status === 'ok' ? 'connected' : 'unexpected response'))
      .catch(() => setBackendStatus('unreachable — start the backend'))
  }, [])

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [progressLog])

  async function handleRunSearch() {
    setRunning(true)
    setProgressLog([])

    try {
      const response = await fetch(`${BACKEND_URL}/run`, { method: 'POST' })

      if (!response.ok) {
        setProgressLog((prev) => [...prev, `Error: HTTP ${response.status}`])
        setRunning(false)
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // SSE lines are separated by double newlines; process complete events
        const parts = buffer.split('\n\n')
        buffer = parts.pop() // keep any incomplete chunk

        for (const part of parts) {
          const dataLine = part.split('\n').find((l) => l.startsWith('data:'))
          if (!dataLine) continue

          try {
            const payload = JSON.parse(dataLine.slice(5).trim())
            const label = formatEvent(payload)
            if (label) setProgressLog((prev) => [...prev, label])

            if (payload.event === 'run_complete' || payload.event === 'run_failed') {
              setRunning(false)
            }
          } catch {
            // ignore malformed lines
          }
        }
      }
    } catch (err) {
      setProgressLog((prev) => [...prev, `Connection error: ${err.message}`])
    } finally {
      setRunning(false)
    }
  }

  function formatEvent(payload) {
    switch (payload.event) {
      case 'run_started':
        return 'Run started.'
      case 'scraping_started':
        return 'Scraping Indeed…'
      case 'scraping_complete':
        return `Scraping complete — ${payload.count} job(s) found.`
      case 'filtering_complete':
        return `Keyword filter complete — ${payload.count} job(s) passed.`
      case 'run_complete':
        return `Run complete (run #${payload.run_id}).`
      case 'run_failed':
        return `Run failed: ${payload.message}`
      default:
        return null
    }
  }

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
            <p style={{ color: '#6b7280', fontSize: 14, marginBottom: 12 }}>
              Scrapes Indeed for the last 24 hours using your search config, applies keyword
              filters, and stores results.
            </p>
            <button
              onClick={handleRunSearch}
              disabled={running}
              style={{
                padding: '8px 20px',
                fontSize: 14,
                cursor: running ? 'not-allowed' : 'pointer',
                opacity: running ? 0.6 : 1,
                background: '#2563eb',
                color: '#fff',
                border: 'none',
                borderRadius: 4,
              }}
            >
              {running ? 'Running…' : 'Run Search'}
            </button>

            {progressLog.length > 0 && (
              <div
                style={{
                  marginTop: 16,
                  background: '#f9fafb',
                  border: '1px solid #e5e7eb',
                  borderRadius: 4,
                  padding: '12px 16px',
                  fontFamily: 'monospace',
                  fontSize: 13,
                  maxHeight: 300,
                  overflowY: 'auto',
                }}
              >
                {progressLog.map((line, i) => (
                  <div key={i} style={{ marginBottom: 4 }}>
                    {line}
                  </div>
                ))}
                <div ref={logEndRef} />
              </div>
            )}
          </section>
        </>
      )}

      {page === 'search-config' && <SearchConfigPage />}
    </div>
  )
}

export default App
