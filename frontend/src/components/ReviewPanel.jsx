import { useState } from 'react'

export default function ReviewPanel({ detection, onClose, onVerified }) {
  const [action, setAction] = useState(null)
  const [correctedSpecies, setCorrectedSpecies] = useState('')
  const [correctedScientific, setCorrectedScientific] = useState('')
  const [reprocessDetector, setReprocessDetector] = useState('speciesnet')
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const pct = Math.round(detection.confidence * 100)
  const displaySpecies = detection.species_name +
    (detection.species_scientific ? ` (${detection.species_scientific})` : '')

  const submit = async (chosenAction) => {
    setSubmitting(true)
    setError(null)

    const body = { action: chosenAction, notes: notes || undefined }
    if (chosenAction === 'correct') {
      body.verified_species = correctedSpecies
      body.verified_species_scientific = correctedScientific || undefined
    }
    if (chosenAction === 'reprocess') {
      body.detector_id = reprocessDetector
    }

    try {
      const res = await fetch(`/api/detections/${detection.id}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || `Server error ${res.status}`)
      }
      const updated = await res.json()
      onVerified(updated)
    } catch (err) {
      setError(err.message)
      setSubmitting(false)
    }
  }

  return (
    <div className="review-overlay" onClick={onClose}>
      <div className="review-panel" onClick={(e) => e.stopPropagation()}>
        <button className="review-close" onClick={onClose} aria-label="Close">✕</button>

        <div className="review-media">
          <img src={detection.frame_url} alt={detection.species_name} />
          {detection.media_type === 'video' && (
            <p className="review-media-label">Video frame</p>
          )}
        </div>

        <div className="review-details">
          <h2>Review Detection</h2>

          <div className="review-prediction">
            <p className="review-label">AI Prediction</p>
            <p className="review-species">{displaySpecies}</p>
            <div className="confidence-bar" style={{ maxWidth: '100%' }}>
              <div className="confidence-fill" style={{ width: `${pct}%` }} />
            </div>
            <p className="confidence-label">{pct}% confidence</p>
            {detection.detector_id && (
              <p className="review-detector">
                Detector: <strong>{detection.detector_id}</strong>
                {detection.detector_version && ` v${detection.detector_version}`}
              </p>
            )}
          </div>

          {error && <p className="review-error">{error}</p>}

          {/* Correction form */}
          {action === 'correct' && (
            <div className="review-correct-form">
              <label>
                Correct species (common name)
                <input
                  type="text"
                  value={correctedSpecies}
                  onChange={(e) => setCorrectedSpecies(e.target.value)}
                  placeholder="e.g. Eastern Quoll"
                  autoFocus
                />
              </label>
              <label>
                Scientific name (optional)
                <input
                  type="text"
                  value={correctedScientific}
                  onChange={(e) => setCorrectedScientific(e.target.value)}
                  placeholder="e.g. Dasyurus viverrinus"
                />
              </label>
            </div>
          )}

          {/* Reprocess detector picker */}
          {action === 'reprocess' && (
            <div className="review-reprocess-form">
              <label>
                Re-run with detector
                <select
                  value={reprocessDetector}
                  onChange={(e) => setReprocessDetector(e.target.value)}
                >
                  <option value="placeholder">Placeholder</option>
                  <option value="speciesnet">SpeciesNet v4</option>
                </select>
              </label>
            </div>
          )}

          {/* Notes field (always available once an action is chosen) */}
          {action && (
            <label className="review-notes-label">
              Notes (optional)
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Reviewer notes…"
                rows={2}
              />
            </label>
          )}

          <div className="review-actions">
            <button
              className="btn btn-confirm"
              disabled={submitting}
              onClick={() => { setAction('confirm'); submit('confirm') }}
            >
              ✅ Confirm
            </button>
            <button
              className="btn btn-correct"
              disabled={submitting}
              onClick={() => setAction(action === 'correct' ? null : 'correct')}
            >
              ✏️ Correct
            </button>
            <button
              className="btn btn-reprocess"
              disabled={submitting}
              onClick={() => setAction(action === 'reprocess' ? null : 'reprocess')}
            >
              🔄 Re-run
            </button>
            <button
              className="btn btn-reject"
              disabled={submitting}
              onClick={() => { setAction('reject'); submit('reject') }}
            >
              ❌ Reject
            </button>
          </div>

          {/* Submit button for actions that need extra input */}
          {(action === 'correct' || action === 'reprocess') && (
            <button
              className="btn btn-submit"
              disabled={submitting || (action === 'correct' && !correctedSpecies.trim())}
              onClick={() => submit(action)}
            >
              {submitting ? 'Submitting…' : 'Submit'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
