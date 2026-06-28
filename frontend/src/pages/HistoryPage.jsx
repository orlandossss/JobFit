import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import styles from './HistoryPage.module.css'

const API_BASE = 'http://localhost:8000'

function formatDate(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function StatusBadge({ status }) {
  const cls =
    status === 'complete'
      ? styles.badgeComplete
      : status === 'scored'
      ? styles.badgeScored
      : status === 'scraped'
      ? styles.badgeScraped
      : styles.badgePending

  return <span className={`${styles.badge} ${cls}`}>{status}</span>
}

export default function HistoryPage() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API_BASE}/runs`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        setRuns(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className={styles.page}>
        <p>Loading history...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <h1>Run History</h1>
          <Link to="/" className={styles.navLink}>Home</Link>
        </div>
        <div className={styles.errorBox}>
          <strong>Error loading history:</strong> {error}
        </div>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Run History</h1>
        <Link to="/" className={styles.navLink}>Home</Link>
      </div>

      {runs.length === 0 ? (
        <p className={styles.empty}>
          No runs yet — click <Link to="/" className={styles.inlineLink}>Run Search</Link> to get started.
        </p>
      ) : (
        <div className={styles.runList}>
          {runs.map((run) => (
            <Link
              key={run.id}
              to={`/results/${run.id}`}
              className={styles.runCard}
            >
              <div className={styles.runInfo}>
                <span className={styles.runDate}>{formatDate(run.date)}</span>
                <StatusBadge status={run.status} />
              </div>
              <div className={styles.runMeta}>
                <span>{run.jobs_selected ?? 0} job(s) processed</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
