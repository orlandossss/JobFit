import { useState, useEffect } from 'react'

const BACKEND_URL = 'http://localhost:8000'

function PersonaPage() {
  const [persona, setPersona] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${BACKEND_URL}/persona`)
      .then((res) => {
        if (res.status === 404) {
          setNotFound(true)
          setLoading(false)
          return null
        }
        if (!res.ok) {
          throw new Error(`Unexpected response: ${res.status}`)
        }
        return res.json()
      })
      .then((data) => {
        if (data !== null) {
          setPersona(data)
          setLoading(false)
        }
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div style={styles.container}>
        <h1>Persona</h1>
        <p>Loading...</p>
      </div>
    )
  }

  if (notFound) {
    return (
      <div style={styles.container}>
        <h1>Persona</h1>
        <p style={styles.hint}>
          No persona found. Run the{' '}
          <code>/build-persona</code> skill in Claude Code to get started.
        </p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={styles.container}>
        <h1>Persona</h1>
        <p style={styles.error}>Error loading persona: {error}</p>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <h1>Persona</h1>
      <pre style={styles.pre}>{JSON.stringify(persona, null, 2)}</pre>
    </div>
  )
}

const styles = {
  container: {
    fontFamily: 'sans-serif',
    maxWidth: 640,
    margin: '80px auto',
    padding: '0 24px',
  },
  hint: {
    color: '#555',
    lineHeight: 1.6,
  },
  error: {
    color: '#c00',
  },
  pre: {
    background: '#f4f4f4',
    border: '1px solid #ddd',
    borderRadius: 4,
    padding: '16px',
    overflowX: 'auto',
    fontSize: 13,
    lineHeight: 1.5,
  },
}

export default PersonaPage
