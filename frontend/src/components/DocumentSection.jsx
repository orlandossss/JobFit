import { useState } from 'react'
import styles from './DocumentSection.module.css'

export default function DocumentSection({ label, content, loading, filename }) {
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    if (!content) return
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  function handleDownload() {
    if (!content) return
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className={styles.section}>
      <div className={styles.docHeader}>
        <span className={styles.docLabel}>{label}</span>
        <div className={styles.docActions}>
          <button
            className={styles.actionButton}
            onClick={handleCopy}
            disabled={!content || loading}
            title="Copy to clipboard"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
          <button
            className={styles.actionButton}
            onClick={handleDownload}
            disabled={!content || loading}
            title={`Download as ${filename}`}
          >
            Download
          </button>
        </div>
      </div>

      {loading ? (
        <div className={styles.loading}>Loading...</div>
      ) : content ? (
        <pre className={styles.docText}>{content}</pre>
      ) : (
        <div className={styles.empty}>No content available.</div>
      )}
    </div>
  )
}
