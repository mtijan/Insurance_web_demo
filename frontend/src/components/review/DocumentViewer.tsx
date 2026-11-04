import { useState } from 'react'
import type { Document } from '../../types/assurance'

export function DocumentViewer({ id, documents }: { id: string; documents: Document[] }) {
  const [index, setIndex] = useState(0)
  const [zoom, setZoom] = useState(1), [angle, setAngle] = useState(0), [brightness, setBrightness] = useState(100)
  const [failed, setFailed] = useState(false), [attempt, setAttempt] = useState(0)
  const current = documents[Math.min(index, documents.length - 1)]
  const [ratio, setRatio] = useState(1)
  function reset() { setZoom(1); setAngle(0); setBrightness(100) }
  function move(next: number) { setIndex(next); reset(); setFailed(false) }
  return <section className="panel viewer" aria-label="Penampil dokumen">
    <h2>Periksa dokumen</h2>
    {!current ? <p>Belum ada dokumen tersimpan.</p> : <>
      <label><span id="document-select-label">Dokumen</span><select aria-labelledby="document-select-label" value={Math.min(index, documents.length - 1)} onChange={e => move(Number(e.target.value))}>{documents.map((doc, i) => <option key={doc.id} value={i}>{doc.document_type.replaceAll('_', ' ')} · {i + 1}</option>)}</select></label>
      <div className="actions viewer-tools"><button className="secondary" disabled={zoom >= 3} onClick={() => setZoom(z => Math.min(3, z + .25))}>Perbesar</button><button className="secondary" disabled={zoom <= .5} onClick={() => setZoom(z => Math.max(.5, z - .25))}>Perkecil</button><button className="secondary" onClick={() => setAngle(a => (a + 90) % 360)}>Putar 90°</button><button className="secondary" onClick={reset}>Reset tampilan</button></div>
      <label>Kecerahan {brightness}%<input aria-label="Kecerahan dokumen" type="range" min={50} max={200} step={10} value={brightness} onChange={e => setBrightness(Number(e.target.value))} /></label>
      <p role="status">Zoom {Math.round(zoom * 100)}% · Rotasi {angle}° · {index + 1} dari {documents.length}</p>
      {failed ? <div className="error" role="alert">Gambar gagal dimuat. <button onClick={() => { setFailed(false); setAttempt(n => n + 1) }}>Coba muat gambar</button></div> : <div className="viewer-canvas" tabIndex={0} aria-label="Area gambar; gulir untuk bagian yang diperbesar"><div className="viewer-stage" style={{ width: `${zoom * 100}%` }}><img width={1080} height={1080} key={`${current.id}:${attempt}`} src={`/api/v1/assurances/${id}/documents/${current.id}/view/?attempt=${attempt}`} alt={`Dokumen ${current.document_type.replaceAll('_', ' ')}`} onError={() => setFailed(true)} onLoad={e => setRatio(e.currentTarget.naturalWidth / e.currentTarget.naturalHeight)} style={{ width: `${ratio >= 1 ? 100 : ratio * 100}%`, height: `${ratio >= 1 ? 100 / ratio : 100}%`, transform: `translate(-50%, -50%) rotate(${angle}deg)`, filter: `brightness(${brightness}%)` }} /></div></div>}
      <a href={`/api/v1/assurances/${id}/documents/${current.id}/view/`} target="_blank" rel="noreferrer">Buka ukuran asli (tab baru)</a>
      <div className="actions"><button className="secondary" disabled={index <= 0} onClick={() => move(index - 1)}>Dokumen sebelumnya</button><button className="secondary" disabled={index >= documents.length - 1} onClick={() => move(index + 1)}>Dokumen berikutnya</button></div>
    </>}
  </section>
}
