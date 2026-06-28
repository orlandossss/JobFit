import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import JobCard from '../components/JobCard.jsx'
import styles from './ResultsPage.module.css'

const API_BASE = 'http://localhost:8000'

export default function ResultsPage() {
  const { runId } = useParams()
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API_BASE}/runs/${runId}/results`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        setJobs(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [runId])

  if (loading) {
    return (
      <div className={styles.page}>
        <p>Loading results...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.page}>
        <div className={styles.errorBox}>
          <strong>Error loading results:</strong> {error}
        </div>
        <Link to="/" className={styles.backLink}>Back to search</Link>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Results — Run #{runId}</h1>
        <Link to="/" className={styles.backLink}>New search</Link>
      </div>

      {jobs.length === 0 ? (
        <p className={styles.empty}>No selected jobs found for this run.</p>
      ) : (
        <div className={styles.jobList}>
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} runId={runId} />
          ))}
        </div>
      )}
    </div>
  )
}
