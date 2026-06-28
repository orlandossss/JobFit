import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import styles from './RunPage.module.css'

const API_BASE = 'http://localhost:8000'

export default function RunPage() {
  const [running, setRunning] = useState(false)
  const [events, setEvents] = useState([])
  const [error, setError] = useState(null)
  const navigate = useNavigate()
  const eventsEndRef = useRef(null)

  function addEvent(msg) {
    setEvents((prev) => [...prev, msg])
    setTimeout(() => eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
  }

  function handleStart() {
    setRunning(true)
    setEvents([])
    setError(null)

    const response = fetch(`${API_BASE}/run`, { method: 'POST' })

    response
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        function pump() {
          return reader.read().then(({ done, value }) => {
            if (done) {
              setRunning(false)
              return
            }
            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop()

            for (const line of lines) {
              const trimmed = line.trim()
              if (trimmed.startsWith('data:')) {
                const json = trimmed.slice(5).trim()
                if (!json) continue
                try {
                  const payload = JSON.parse(json)
                  const eventType = payload.event

                  if (eventType === 'run_complete') {
                    addEvent(`Run complete! Navigating to results...`)
                    setRunning(false)
                    setTimeout(() => navigate(`/results/${payload.run_id}`), 800)
                    return
                  }

                  if (eventType === 'run_failed') {
                    addEvent(`Error: ${payload.message}`)
                    setError(payload.message)
                    setRunning(false)
                    return
                  }

                  addEvent(formatEvent(payload))
                } catch {
                  // ignore malformed lines
                }
              }
            }
            return pump()
          })
        }

        return pump()
      })
      .catch((err) => {
        setError(err.message)
        setRunning(false)
      })
  }

  return (
    <div className={styles.page}>
      <h1>JobFit</h1>
      <p className={styles.subtitle}>
        Automated job search, scoring, and tailored document generation.
      </p>

      <button
        className={styles.runButton}
        onClick={handleStart}
        disabled={running}
      >
        {running ? 'Running...' : 'Run Search'}
      </button>

      {error && (
        <div className={styles.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {events.length > 0 && (
        <div className={styles.log}>
          <h2>Progress</h2>
          <ul className={styles.eventList}>
            {events.map((msg, i) => (
              <li key={i} className={styles.eventItem}>
                {msg}
              </li>
            ))}
          </ul>
          <div ref={eventsEndRef} />
        </div>
      )}
    </div>
  )
}

function formatEvent(payload) {
  switch (payload.event) {
    case 'run_started':
      return 'Pipeline started'
    case 'scraping_started':
      return 'Scraping Indeed...'
    case 'scraping_complete':
      return `Scraped ${payload.count} job(s)`
    case 'filtering_complete':
      return `After keyword filter: ${payload.count} job(s) remain`
    case 'scoring_job':
      return `Scored: ${payload.title} — ${payload.score}/10`
    case 'scoring_complete':
      return `Scoring done. Top ${payload.count} job(s) selected`
    case 'generating_cv':
      return `Generating CV for ${payload.company} — ${payload.title}...`
    case 'generating_cover_letter':
      return `Generating cover letter for ${payload.company} — ${payload.title}...`
    default:
      return JSON.stringify(payload)
  }
}
