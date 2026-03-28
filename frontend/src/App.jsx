import { useEffect, useRef, useState } from 'react'
import Dashboard from './components/Dashboard'
import DetectionResult from './components/DetectionResult'
import ReviewPanel from './components/ReviewPanel'
import UploadForm from './components/UploadForm'

const STATUS_FILTERS = ['all', 'pending', 'verified', 'rejected']
const TABS = ['feed', 'dashboard']

const CONFIDENCE_OPTIONS = [
  { label: 'All', value: 0 },
  { label: '≥ 50%', value: 0.5 },
  { label: '≥ 70%', value: 0.7 },
  { label: '≥ 90%', value: 0.9 },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('feed')
  const [latestDetection, setLatestDetection] = useState(null)
  const [detections, setDetections] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('all')
  const [reviewing, setReviewing] = useState(null)
  const [minConfidence, setMinConfidence] = useState(0)
  const [pendingCount, setPendingCount] = useState(0)

  const feedRef = useRef(null)

  const fetchDetections = async (statusFilter = 'all') => {
    const url = statusFilter === 'all'
      ? '/api/detections/'
      : `/api/detections/?status=${statusFilter}`
    const res = await fetch(url)
    const data = await res.json()
    setDetections(data)
  }

  // Keep a live pending count independent of the current filter
  const refreshPendingCount = async () => {
    try {
      const res = await fetch('/api/stats/overview')
      const data = await res.json()
      setPendingCount(data.pending_count ?? 0)
    } catch {
      // non-critical — ignore
    }
  }

  useEffect(() => {
    fetchDetections(filter)
    refreshPendingCount()
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
      refreshPendingCount()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleVerified = (updated) => {
    setReviewing(null)
    setDetections((prev) => prev.map((d) => d.id === updated.id ? updated : d))
    if (latestDetection?.id === updated.id) setLatestDetection(updated)
    fetchDetections(filter)
    refreshPendingCount()
  }

  const handlePendingBadgeClick = () => {
    setActiveTab('feed')
    setFilter('pending')
    // Scroll feed into view after state updates
    setTimeout(() => feedRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
  }

  const visibleDetections = minConfidence > 0
    ? detections.filter(d => d.confidence >= minConfidence)
    : detections

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
              onClick={handlePendingBadgeClick}
              title="Show pending detections"
            >
              {pendingCount} pending review
            </button>
          )}
        </div>

        {/* Main navigation tabs */}
        <div className="main-tabs">
          {TABS.map(tab => (
            <button
              key={tab}
              className={`main-tab${activeTab === tab ? ' active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </header>

      <main>
        {activeTab === 'dashboard' ? (
          <Dashboard />
        ) : (
          <>
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

            <div className="feed-header" ref={feedRef}>
              <h2>Detections</h2>
              <div className="feed-controls">
                <div className="filter-tabs">
                  {STATUS_FILTERS.map((f) => (
                    <button
                      key={f}
                      className={`filter-tab${filter === f ? ' active' : ''}`}
                      onClick={() => setFilter(f)}
                    >
                      {f.charAt(0).toUpperCase() + f.slice(1)}
                    </button>
                  ))}
                </div>
                <div className="confidence-filter">
                  <label htmlFor="conf-select">Min confidence</label>
                  <select
                    id="conf-select"
                    value={minConfidence}
                    onChange={e => setMinConfidence(Number(e.target.value))}
                  >
                    {CONFIDENCE_OPTIONS.map(({ label, value }) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {visibleDetections.length === 0 ? (
              <p className="empty-state">
                {filter === 'all'
                  ? 'No detections yet. Upload an image or video to get started.'
                  : `No ${filter} detections.`}
              </p>
            ) : (
              visibleDetections.map((d) => (
                <DetectionResult key={d.id} detection={d} onReview={setReviewing} />
              ))
            )}
          </>
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
