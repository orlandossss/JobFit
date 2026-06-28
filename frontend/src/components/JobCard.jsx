import { useState } from 'react'
import DocumentSection from './DocumentSection.jsx'
import styles from './JobCard.module.css'

const API_BASE = 'http://localhost:8000'

// Sentinel used to distinguish "file not found on disk" from other errors
const FILE_NOT_FOUND = '__FILE_NOT_FOUND__'

export default function JobCard({ job, runId }) {
  const [cvExpanded, setCvExpanded] = useState(false)
  const [clExpanded, setClExpanded] = useState(false)
  const [cvContent, setCvContent] = useState(null)
  const [clContent, setClContent] = useState(null)
  const [cvLoading, setCvLoading] = useState(false)
  const [clLoading, setClLoading] = useState(false)

  function loadCv() {
    if (cvContent !== null) return
    setCvLoading(true)
    fetch(`${API_BASE}/runs/${runId}/jobs/${job.id}/cv`)
      .then((r) => {
        if (r.status === 404) return Promise.resolve({ _notFound: true })
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((data) => {
        setCvContent(data._notFound ? FILE_NOT_FOUND : data.content)
        setCvLoading(false)
      })
      .catch(() => {
        setCvContent('Error loading CV.')
        setCvLoading(false)
      })
  }

  function loadCl() {
    if (clContent !== null) return
    setClLoading(true)
    fetch(`${API_BASE}/runs/${runId}/jobs/${job.id}/cover-letter`)
      .then((r) => {
        if (r.status === 404) return Promise.resolve({ _notFound: true })
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((data) => {
        setClContent(data._notFound ? FILE_NOT_FOUND : data.content)
        setClLoading(false)
      })
      .catch(() => {
        setClContent('Error loading cover letter.')
        setClLoading(false)
      })
  }

  function handleToggleCv() {
    if (!cvExpanded) loadCv()
    setCvExpanded((v) => !v)
  }

  function handleToggleCl() {
    if (!clExpanded) loadCl()
    setClExpanded((v) => !v)
  }

  const score = job.score ? Math.round(job.score) : '—'
  const scoreColor = score >= 8 ? '#16a34a' : score >= 5 ? '#ca8a04' : '#dc2626'

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <div className={styles.jobInfo}>
          <h2 className={styles.title}>{job.title}</h2>
          <div className={styles.company}>{job.company}</div>
          {job.location && <div className={styles.location}>{job.location}</div>}
        </div>
        <div className={styles.scoreBadge} style={{ color: scoreColor }}>
          {score}<span className={styles.scoreMax}>/10</span>
        </div>
      </div>

      {job.reasoning && (
        <p className={styles.reasoning}>{job.reasoning}</p>
      )}

      <div className={styles.docSection}>
        <button
          className={styles.toggleButton}
          onClick={handleToggleCv}
          aria-expanded={cvExpanded}
        >
          {cvExpanded ? 'Hide CV' : 'Show CV'}
        </button>
        {cvExpanded && (
          <DocumentSection
            label="Tailored CV"
            content={cvContent}
            loading={cvLoading}
            filename={`${job.company?.toLowerCase().replace(/\s+/g, '_') ?? 'job'}_cv.txt`}
          />
        )}
      </div>

      <div className={styles.docSection}>
        <button
          className={styles.toggleButton}
          onClick={handleToggleCl}
          aria-expanded={clExpanded}
        >
          {clExpanded ? 'Hide Cover Letter' : 'Show Cover Letter'}
        </button>
        {clExpanded && (
          <DocumentSection
            label="Tailored Cover Letter"
            content={clContent}
            loading={clLoading}
            filename={`${job.company?.toLowerCase().replace(/\s+/g, '_') ?? 'job'}_cover_letter.txt`}
          />
        )}
      </div>
    </div>
  )
}
