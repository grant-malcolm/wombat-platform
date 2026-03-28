const STATUS_CONFIG = {
  pending:     { label: 'Pending',    className: 'status-pending' },
  verified:    { label: 'Verified',   className: 'status-verified' },
  rejected:    { label: 'Rejected',   className: 'status-rejected' },
  reprocessing:{ label: 'Re-running', className: 'status-reprocessing' },
}

export default function DetectionResult({ detection, featured = false, onReview }) {
  const pct = Math.round(detection.confidence * 100)
  const mediaLabel = detection.media_type === 'video' ? 'Video frame' : 'Image'
  const timestamp = new Date(detection.created_at).toLocaleString()
  const status = detection.status || 'pending'
  const { label: statusLabel, className: statusClass } = STATUS_CONFIG[status] ?? STATUS_CONFIG.pending

  const displaySpecies = detection.verified_species
    ? `${detection.verified_species}${detection.verified_species_scientific ? ` (${detection.verified_species_scientific})` : ''}`
    : detection.species_name + (detection.species_scientific ? ` (${detection.species_scientific})` : '')

  return (
    <div className={`detection-card${featured ? ' featured' : ''}`}>
      <img src={detection.frame_url} alt={detection.species_name} />
      <div className="detection-info">
        <div className="detection-header">
          <h3>{displaySpecies}</h3>
          <span className={`status-badge ${statusClass}`}>{statusLabel}</span>
        </div>
        <div className="confidence-bar">
          <div className="confidence-fill" style={{ width: `${pct}%` }} />
        </div>
        <p className="confidence-label">{pct}% confidence</p>
        {detection.detector_id && (
          <p className="detection-detector">
            {detection.detector_id}
            {detection.detector_version ? ` v${detection.detector_version}` : ''}
          </p>
        )}
        <p className="detection-meta">
          {mediaLabel} &middot; {detection.original_filename} &middot; {timestamp}
        </p>
        {status === 'pending' && onReview && (
          <button className="btn btn-review" onClick={() => onReview(detection)}>
            Review
          </button>
        )}
        {status === 'verified' && detection.verified_by && (
          <p className="detection-verified-by">
            Verified by {detection.verified_by}
            {detection.notes ? ` — ${detection.notes}` : ''}
          </p>
        )}
        {status === 'rejected' && detection.notes && (
          <p className="detection-verified-by">Rejected: {detection.notes}</p>
        )}
      </div>
    </div>
  )
}
