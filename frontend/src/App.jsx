import { useEffect, useState } from 'react'
import DetectionResult from './components/DetectionResult'
import UploadForm from './components/UploadForm'

export default function App() {
  const [latestDetection, setLatestDetection] = useState(null)
  const [detections, setDetections] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchDetections = async () => {
    const res = await fetch('/api/detections/')
    const data = await res.json()
    setDetections(data)
  }

  useEffect(() => {
    fetchDetections()
  }, [])

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
      fetchDetections()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header>
        <h1>WOMBAT</h1>
        <p>Wildlife Observation and Monitoring with Biodiversity Aggregation Technology</p>
      </header>

      <main>
        <UploadForm onUpload={handleUpload} loading={loading} />

        {error && (
          <p style={{ color: '#c0392b', marginBottom: '1rem' }}>Upload failed: {error}</p>
        )}

        {latestDetection && (
          <>
            <h2>Latest Detection</h2>
            <DetectionResult detection={latestDetection} featured />
          </>
        )}

        <h2>All Detections</h2>
        {detections.length === 0 ? (
          <p className="empty-state">No detections yet. Upload an image or video to get started.</p>
        ) : (
          detections.map((d) => <DetectionResult key={d.id} detection={d} />)
        )}
      </main>
    </div>
  )
}
