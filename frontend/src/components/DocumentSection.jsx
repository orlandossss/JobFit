import { useState } from 'react'
import styles from './DocumentSection.module.css'

// Must match the sentinel used in JobCard.jsx
const FILE_NOT_FOUND = '__FILE_NOT_FOUND__'

export default function DocumentSection({ label, content, loading, filename }) {
  const [copied, setCopied] = useState(false)

  const isFileMissing = content === FILE_NOT_FOUND
  const hasContent = content && !isFileMissing

  function handleCopy() {
    if (!hasContent) return
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  function handleDownload() {
    if (!hasContent) return
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
            disabled={!hasContent || loading}
            title="Copy to clipboard"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
          <button
            className={styles.actionButton}
            onClick={handleDownload}
            disabled={!hasContent || loading}
            title={`Download as ${filename}`}
          >
            Download
          </button>
        </div>
      </div>

      {loading ? (
        <div className={styles.loading}>Loading...</div>
      ) : isFileMissing ? (
        <div className={styles.fileNotFound}>File not found on disk.</div>
      ) : hasContent ? (
        <pre className={styles.docText}>{content}</pre>
      ) : (
        <div className={styles.empty}>No content available.</div>
      )}
    </div>
  )
}
