import { useState, useEffect } from 'react'

const BACKEND_URL = 'http://localhost:8000'

const DEFAULTS = {
  target_titles: '',
  location: '',
  country: '',
  language: 'en',
  keywords_include: '',
  keywords_exclude: '',
  max_jobs: 5,
}

/**
 * Convert a list (array) to a comma-separated string for display in text inputs.
 */
function listToString(arr) {
  if (!Array.isArray(arr)) return ''
  return arr.join(', ')
}

/**
 * Convert a comma-separated string back to a trimmed, non-empty list.
 */
function stringToList(str) {
  if (!str || !str.trim()) return []
  return str
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}

export default function SearchConfigPage() {
  const [form, setForm] = useState(DEFAULTS)
  const [status, setStatus] = useState(null) // null | 'saving' | 'saved' | 'error'
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    fetch(`${BACKEND_URL}/search-config`)
      .then((res) => res.json())
      .then((data) => {
        setForm({
          target_titles: listToString(data.target_titles),
          location: data.location ?? '',
          country: data.country ?? '',
          language: data.language ?? 'en',
          keywords_include: listToString(data.keywords_include),
          keywords_exclude: listToString(data.keywords_exclude),
          max_jobs: data.max_jobs ?? 5,
        })
      })
      .catch(() => {
        setErrorMsg('Could not load config — is the backend running?')
        setStatus('error')
      })
  }, [])

  function handleChange(e) {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  async function handleSave(e) {
    e.preventDefault()
    setStatus('saving')
    setErrorMsg('')

    const payload = {
      target_titles: stringToList(form.target_titles),
      location: form.location,
      country: form.country,
      language: form.language,
      keywords_include: stringToList(form.keywords_include),
      keywords_exclude: stringToList(form.keywords_exclude),
      max_jobs: parseInt(form.max_jobs, 10) || 5,
    }

    try {
      const res = await fetch(`${BACKEND_URL}/search-config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? `Server error ${res.status}`)
      }

      setStatus('saved')
    } catch (err) {
      setErrorMsg(err.message ?? 'Unknown error')
      setStatus('error')
    }
  }

  const fieldStyle = {
    display: 'block',
    width: '100%',
    padding: '6px 10px',
    fontSize: 14,
    boxSizing: 'border-box',
    marginTop: 4,
    border: '1px solid #ccc',
    borderRadius: 4,
  }

  const labelStyle = {
    display: 'block',
    marginTop: 16,
    fontWeight: 600,
    fontSize: 14,
  }

  const hintStyle = {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  }

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: 640, margin: '0 auto', padding: '24px' }}>
      <h2 style={{ marginTop: 0 }}>Search Config</h2>
      <p style={{ color: '#555', marginBottom: 24 }}>
        Configure the job search parameters. Changes persist to{' '}
        <code>search_config.json</code> on the server.
      </p>

      <form onSubmit={handleSave}>
        <label style={labelStyle}>
          Target job titles
          <input
            name="target_titles"
            value={form.target_titles}
            onChange={handleChange}
            placeholder="Software Engineer, Backend Developer"
            style={fieldStyle}
          />
          <span style={hintStyle}>Comma-separated list of job titles to search for.</span>
        </label>

        <label style={labelStyle}>
          Location
          <input
            name="location"
            value={form.location}
            onChange={handleChange}
            placeholder="Paris, France"
            style={fieldStyle}
          />
        </label>

        <label style={labelStyle}>
          Country
          <input
            name="country"
            value={form.country}
            onChange={handleChange}
            placeholder="France"
            style={fieldStyle}
          />
          <span style={hintStyle}>Country code or name used by the Indeed market (jobspy).</span>
        </label>

        <label style={labelStyle}>
          Language
          <input
            name="language"
            value={form.language}
            onChange={handleChange}
            placeholder="en"
            style={fieldStyle}
          />
          <span style={hintStyle}>Output language for generated documents (e.g. &ldquo;en&rdquo;, &ldquo;fr&rdquo;).</span>
        </label>

        <label style={labelStyle}>
          Keywords to include
          <input
            name="keywords_include"
            value={form.keywords_include}
            onChange={handleChange}
            placeholder="Python, API, FastAPI"
            style={fieldStyle}
          />
          <span style={hintStyle}>
            Comma-separated. A listing must contain at least one of these keywords to pass the
            pre-filter.
          </span>
        </label>

        <label style={labelStyle}>
          Keywords to exclude
          <input
            name="keywords_exclude"
            value={form.keywords_exclude}
            onChange={handleChange}
            placeholder="sales, junior"
            style={fieldStyle}
          />
          <span style={hintStyle}>
            Comma-separated. Any listing containing one of these keywords is discarded.
          </span>
        </label>

        <label style={labelStyle}>
          Max jobs
          <input
            type="number"
            name="max_jobs"
            value={form.max_jobs}
            onChange={handleChange}
            min={1}
            max={100}
            style={{ ...fieldStyle, width: 100 }}
          />
          <span style={hintStyle}>Maximum number of jobs to process through the full pipeline.</span>
        </label>

        <div style={{ marginTop: 28, display: 'flex', alignItems: 'center', gap: 16 }}>
          <button
            type="submit"
            disabled={status === 'saving'}
            style={{
              padding: '8px 20px',
              fontSize: 14,
              cursor: status === 'saving' ? 'not-allowed' : 'pointer',
              opacity: status === 'saving' ? 0.6 : 1,
              background: '#2563eb',
              color: '#fff',
              border: 'none',
              borderRadius: 4,
            }}
          >
            {status === 'saving' ? 'Saving…' : 'Save'}
          </button>

          {status === 'saved' && (
            <span style={{ color: '#16a34a', fontSize: 14 }}>Saved successfully.</span>
          )}
          {status === 'error' && (
            <span style={{ color: '#dc2626', fontSize: 14 }}>
              Error: {errorMsg || 'Could not save config.'}
            </span>
          )}
        </div>
      </form>
    </div>
  )
}
