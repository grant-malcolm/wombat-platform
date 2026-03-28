import { useRef, useState } from 'react'

export default function UploadForm({ onUpload, loading }) {
  const inputRef = useRef()
  const [dragging, setDragging] = useState(false)

  const handleFile = (file) => {
    if (file) onUpload(file)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragging(true)
  }

  const handleDragLeave = () => setDragging(false)

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  return (
    <div
      className={`upload-zone${dragging ? ' dragging' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !loading && inputRef.current.click()}
      role="button"
      aria-label="Upload image or video"
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/quicktime,video/x-msvideo,video/webm"
        onChange={(e) => handleFile(e.target.files[0])}
        style={{ display: 'none' }}
      />
      {loading ? (
        <>
          <div className="spinner" />
          <p>Analysing&hellip;</p>
        </>
      ) : (
        <>
          <p>Drop an image or video here, or click to browse</p>
          <small>JPEG &middot; PNG &middot; WebP &middot; GIF &middot; MP4 &middot; MOV &middot; AVI &middot; WebM</small>
        </>
      )}
    </div>
  )
}
