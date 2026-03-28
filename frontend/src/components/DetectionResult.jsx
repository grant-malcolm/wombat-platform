export default function DetectionResult({ detection, featured = false }) {
  const pct = Math.round(detection.confidence * 100)
  const mediaLabel = detection.media_type === 'video' ? 'Video frame' : 'Image'
  const timestamp = new Date(detection.created_at).toLocaleString()

  return (
    <div className={`detection-card${featured ? ' featured' : ''}`}>
      <img src={detection.frame_url} alt={detection.species_name} />
      <div className="detection-info">
        <h3>{detection.species_name}</h3>
        <div className="confidence-bar">
          <div className="confidence-fill" style={{ width: `${pct}%` }} />
        </div>
        <p className="confidence-label">{pct}% confidence</p>
        <p className="detection-meta">
          {mediaLabel} &middot; {detection.original_filename} &middot; {timestamp}
        </p>
      </div>
    </div>
  )
}
