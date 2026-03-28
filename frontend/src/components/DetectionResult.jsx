const STATUS_CONFIG = {
  pending:     { label: 'Pending',    className: 'status-pending' },
  verified:    { label: 'Verified',   className: 'status-verified' },
  rejected:    { label: 'Rejected',   className: 'status-rejected' },
  reprocessing:{ label: 'Re-running', className: 'status-reprocessing' },
}

function isEmptyDetection(detection) {
  const species = (detection.species_name || '').toLowerCase()
  return species === 'empty' || species === 'blank'
}

function detectorLabel(detection) {
  if (!detection.detector_id) return null
  const id = detection.detector_id
  const ver = detection.detector_version

  if (id === 'megadetector+speciesnet') return `MegaDetector + SpeciesNet${ver ? ` v${ver}` : ''}`
  if (id === 'speciesnet-v4') return `SpeciesNet${ver ? ` v${ver}` : ''}`
  if (id === 'placeholder') return 'Placeholder'
  return `${id}${ver ? ` v${ver}` : ''}`
}

export default function DetectionResult({ detection, featured = false, onReview }) {
  const pct = Math.round(detection.confidence * 100)
  const mediaLabel = detection.media_type === 'video' ? 'Video frame' : 'Image'
  const timestamp = new Date(detection.created_at).toLocaleString()
  const status = detection.status || 'pending'
  const { label: statusLabel, className: statusClass } = STATUS_CONFIG[status] ?? STATUS_CONFIG.pending
  const empty = isEmptyDetection(detection)
  const label = detectorLabel(detection)

  const displaySpecies = detection.verified_species
    ? `${detection.verified_species}${detection.verified_species_scientific ? ` (${detection.verified_species_scientific})` : ''}`
    : detection.species_name + (detection.species_scientific ? ` (${detection.species_scientific})` : '')

  return (
    <div className={`detection-card${featured ? ' featured' : ''}${empty ? ' detection-empty' : ''}`}>
      <img src={detection.frame_url} alt={detection.species_name} />
      <div className="detection-info">
        <div className="detection-header">
          {empty ? (
            <h3 className="detection-empty-label">Empty frame</h3>
          ) : (
            <h3>{displaySpecies}</h3>
          )}
          <span className={`status-badge ${statusClass}`}>{statusLabel}</span>
        </div>

        {!empty && (
          <>
            <div className="confidence-bar">
              <div className="confidence-fill" style={{ width: `${pct}%` }} />
            </div>
            <p className="confidence-label">{pct}% confidence</p>
          </>
        )}

        {label && (
          <span className="detector-badge">{label}</span>
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
