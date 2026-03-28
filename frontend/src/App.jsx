import { useEffect, useState } from 'react'
import DetectionResult from './components/DetectionResult'
import ReviewPanel from './components/ReviewPanel'
import UploadForm from './components/UploadForm'

const FILTERS = ['all', 'pending', 'verified', 'rejected']

export default function App() {
  const [latestDetection, setLatestDetection] = useState(null)
  const [detections, setDetections] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('all')
  const [reviewing, setReviewing] = useState(null)

  const fetchDetections = async (statusFilter = 'all') => {
    const url = statusFilter === 'all'
      ? '/api/detections/'
      : `/api/detections/?status=${statusFilter}`
    const res = await fetch(url)
    const data = await res.json()
    setDetections(data)
  }

  useEffect(() => {
    fetchDetections(filter)
  }, [filter])

  const handleUpload = async (file) => {
    setLoading(true)
    setError(null)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch('/api/detections/upload', {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Server error ${res.status}`)
      }
      const detection = await res.json()
      setLatestDetection(detection)
      fetchDetections(filter)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleVerified = (updated) => {
    setReviewing(null)
    // Replace in list
    setDetections((prev) => prev.map((d) => d.id === updated.id ? updated : d))
    if (latestDetection?.id === updated.id) setLatestDetection(updated)
    // Refetch to respect active filter
    fetchDetections(filter)
  }

  const pendingCount = detections.filter((d) => (d.status || 'pending') === 'pending').length

  return (
    <div className="app">
      <header>
        <div className="header-content">
          <div>
            <h1>WOMBAT</h1>
            <p>Wildlife Observation and Monitoring with Biodiversity Aggregation Technology</p>
          </div>
          {pendingCount > 0 && (
            <button
              className="pending-badge"
              onClick={() => setFilter('pending')}
              title="Show pending detections"
            >
              {pendingCount} pending review
            </button>
          )}
        </div>
      </header>

      <main>
        <UploadForm onUpload={handleUpload} loading={loading} />

        {error && (
          <p style={{ color: '#c0392b', marginBottom: '1rem' }}>Upload failed: {error}</p>
        )}

        {latestDetection && (
          <>
            <h2>Latest Detection</h2>
            <DetectionResult
              detection={latestDetection}
              featured
              onReview={setReviewing}
            />
          </>
        )}

        <div className="feed-header">
          <h2>Detections</h2>
          <div className="filter-tabs">
            {FILTERS.map((f) => (
              <button
                key={f}
                className={`filter-tab${filter === f ? ' active' : ''}`}
                onClick={() => setFilter(f)}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {detections.length === 0 ? (
          <p className="empty-state">
            {filter === 'all'
              ? 'No detections yet. Upload an image or video to get started.'
              : `No ${filter} detections.`}
          </p>
        ) : (
          detections.map((d) => (
            <DetectionResult key={d.id} detection={d} onReview={setReviewing} />
          ))
        )}
      </main>

      {reviewing && (
        <ReviewPanel
          detection={reviewing}
          onClose={() => setReviewing(null)}
          onVerified={handleVerified}
        />
      )}
    </div>
  )
}
