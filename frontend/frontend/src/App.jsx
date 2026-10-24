import { useEffect, useState } from 'react'
import { Activity, CarFront, Upload, RefreshCw, Database, Video, AlertCircle } from 'lucide-react'

const API = 'http://127.0.0.1:8000'

function StatCard({ title, value, icon: Icon, detail }) {
  return <div className="stat-card">
    <div className="stat-top"><span>{title}</span><Icon size={20} /></div>
    <div className="stat-value">{value}</div>
    <div className="stat-detail">{detail}</div>
  </div>
}

export default function App() {
  const [stats, setStats] = useState({ total_detections: 0, by_type: [], by_color: [] })
  const [detections, setDetections] = useState([])
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [apiOnline, setApiOnline] = useState(false)

  async function refresh() {
    try {
      const [health, s, d] = await Promise.all([
        fetch(`${API}/api/health`), fetch(`${API}/api/stats`), fetch(`${API}/api/detections?limit=30`)
      ])
      if (!health.ok || !s.ok || !d.ok) throw new Error('API returned an error')
      setApiOnline(true)
      setStats(await s.json())
      setDetections(await d.json())
      setError('')
    } catch {
      setApiOnline(false)
      setError('Backend is not reachable. Start it with: python -m uvicorn backend.main:app --reload')
    }
  }

  useEffect(() => { refresh() }, [])

  async function uploadVideo(event) {
    event.preventDefault()
    if (!file) { setError('Please choose a video file first.'); return }
    setBusy(true); setError(''); setMessage('Processing video. This can take a while on a CPU...')
    setResult(null)
    try {
      const body = new FormData()
      body.append('file', file)
      const response = await fetch(`${API}/api/process-video`, { method: 'POST', body })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Processing failed')
      setResult(data)
      setMessage(`Finished: ${data.frames_processed} frames processed.`)
      await refresh()
    } catch (e) {
      setError(e.message || 'Could not process video.')
      setMessage('')
    } finally { setBusy(false) }
  }

  async function clearHistory() {
    if (!window.confirm('Clear all saved detections?')) return
    try {
      await fetch(`${API}/api/detections`, { method: 'DELETE' })
      setResult(null); await refresh()
    } catch { setError('Could not clear history.') }
  }

  const byType = stats.by_type || []
  const byColor = stats.by_color || []

  return <main className="app-shell">
    <header className="topbar">
      <div className="brand-mark"><CarFront size={26} /></div>
      <div className="brand-text"><h1>Vehicle<span>Analytics</span></h1><p>REAL-TIME VIDEO INTELLIGENCE · CPU PROTOTYPE</p></div>
      <div className={`status ${apiOnline ? 'online' : 'offline'}`}><span />{apiOnline ? 'API Connected' : 'API Offline'}</div>
    </header>

    <section className="welcome">
      <div><p className="eyebrow">OVERVIEW</p><h2>Vehicle Analytics Dashboard</h2><p className="subtext">Upload traffic footage to detect vehicles, estimate their color, and save detection events.</p></div>
      <button className="secondary-button" onClick={refresh}><RefreshCw size={16}/> Refresh</button>
    </section>

    {error && <div className="alert error"><AlertCircle size={18}/>{error}</div>}
    {message && <div className="alert success"><Activity size={18}/>{message}</div>}

    <section className="stats-grid">
      <StatCard title="Total detections" value={stats.total_detections ?? 0} icon={CarFront} detail="Saved detection events"/>
      <StatCard title="Vehicle types" value={byType.length} icon={Activity} detail="Types detected so far"/>
      <StatCard title="Color categories" value={byColor.length} icon={Database} detail="Approximate color labels"/>
      <StatCard title="Processing mode" value="CPU" icon={Video} detail="YOLO11 nano model"/>
    </section>

    <section className="content-grid">
      <div className="panel upload-panel">
        <div className="panel-heading"><div><h3>Process a traffic video</h3><p>Supported formats: MP4, AVI, MOV, MKV, WEBM</p></div><Upload size={21}/></div>
        <form onSubmit={uploadVideo}>
          <label className="dropzone">
            <input type="file" accept="video/mp4,video/quicktime,video/x-msvideo,video/webm,.mkv" onChange={e => {setFile(e.target.files?.[0] || null); setMessage(''); setError('')}}/>
            <div className="upload-icon"><Upload size={25}/></div>
            <strong>{file ? file.name : 'Choose a video file'}</strong>
            <span>{file ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : 'Click here to browse your computer'}</span>
          </label>
          <button className="primary-button" disabled={busy || !apiOnline}>{busy ? 'Processing video…' : 'Start vehicle detection'}</button>
        </form>
        <p className="hint">Tip: start with a short 5–15 second clip. CPU processing may be slow.</p>
      </div>

      <div className="panel">
        <div className="panel-heading"><div><h3>Vehicle breakdown</h3><p>Detection events by class</p></div><Activity size={21}/></div>
        {byType.length ? <div className="breakdown">{byType.map(item => <div className="bar-row" key={item.name}><div><span>{item.name}</span><b>{item.count}</b></div><div className="bar"><span style={{width: `${Math.max(4, item.count / Math.max(...byType.map(x => x.count)) * 100)}%`}}/></div></div>)}</div> : <div className="empty">No vehicle detections yet. Upload a video to begin.</div>}
        <div className="color-list"><h4>Estimated colors</h4>{byColor.length ? byColor.map(c => <span className="chip" key={c.name}>{c.name} <b>{c.count}</b></span>) : <p className="muted">Color results will appear here.</p>}</div>
      </div>
    </section>

    {result && <section className="panel result-panel">
      <div className="panel-heading"><div><h3>Latest processed video</h3><p>{result.frames_processed} frames · {result.vehicle_detections} detection events</p></div></div>
      <video controls src={`${API}${result.video_url}`} />
      <p className="muted">Output video is saved by the backend in sample_videos/processed.</p>
    </section>}

    <section className="panel table-panel">
      <div className="panel-heading"><div><h3>Recent detection events</h3><p>Stored locally in SQLite</p></div><button className="text-button" onClick={clearHistory}>Clear history</button></div>
      <div className="table-wrap"><table><thead><tr><th>Time</th><th>Vehicle</th><th>Estimated color</th><th>Confidence</th><th>Frame</th></tr></thead>
      <tbody>{detections.length ? detections.map(row => <tr key={row.id}><td>{row.timestamp?.replace('T', ' ')}</td><td><span className="vehicle-pill">{row.vehicle_type}</span></td><td>{row.color}</td><td>{(row.confidence * 100).toFixed(1)}%</td><td>{row.frame_number ?? '—'}</td></tr>) : <tr><td colSpan="5" className="empty-cell">No events saved yet.</td></tr>}</tbody></table></div>
    </section>

    <footer><span>Vehicle Analytics · Local prototype</span><span><span className="footer-dot"/> Data stays on this computer</span></footer>
  </main>
}
