import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

function App() {
  const [stats, setStats] = useState({
    total_detections: 0,
    cars: 0,
    trucks: 0,
    buses: 0,
    motorcycles: 0,
    line_crossings: 0,
  });

  const [detections, setDetections] = useState([]);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [health, setHealth] = useState("Checking...");
  const [outputVideo, setOutputVideo] = useState("");

  async function loadDashboard() {
    try {
      const [healthResponse, statsResponse, detectionsResponse] =
        await Promise.all([
          fetch(`${API}/api/health`),
          fetch(`${API}/api/stats`),
          fetch(`${API}/api/detections`),
        ]);

      if (healthResponse.ok) {
        const data = await healthResponse.json();
        setHealth(data.status === "healthy" ? "Online" : "Unavailable");
      } else {
        setHealth("Unavailable");
      }

      if (statsResponse.ok) {
        const data = await statsResponse.json();
        setStats((previous) => ({ ...previous, ...data }));
      }

      if (detectionsResponse.ok) {
        const data = await detectionsResponse.json();
        setDetections(Array.isArray(data) ? data : data.detections || []);
      }
    } catch {
      setHealth("Offline");
    }
  }

  useEffect(() => {
    loadDashboard();
    const timer = setInterval(loadDashboard, 5000);
    return () => clearInterval(timer);
  }, []);

  async function processVideo(event) {
    event.preventDefault();

    if (!file) {
      setError("Please select a video file first.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");
    setOutputVideo("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API}/api/process-video`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Video processing failed.");
      }

      setMessage(data.message || "Video request completed.");

      const output = data.output_video || data.output_url || "";
      if (output) {
        setOutputVideo(
          output.startsWith("http")
            ? output
            : `${API}${output.startsWith("/") ? "" : "/"}${output}`
        );
      }

      if (data.stats) {
        setStats((previous) => ({ ...previous, ...data.stats }));
      }

      if (Array.isArray(data.detections)) {
        setDetections(data.detections);
      }

      await loadDashboard();
    } catch (err) {
      setError(`${err.message} Check that the backend is running at ${API}.`);
    } finally {
      setLoading(false);
    }
  }

  const cards = [
    { label: "Total Vehicles", value: stats.total_detections ?? 0, icon: "◈" },
    { label: "Cars", value: stats.cars ?? 0, icon: "🚘" },
    { label: "Trucks", value: stats.trucks ?? 0, icon: "🚚" },
    { label: "Buses", value: stats.buses ?? 0, icon: "🚌" },
    { label: "Motorcycles", value: stats.motorcycles ?? 0, icon: "🏍️" },
    { label: "Line Crossings", value: stats.line_crossings ?? 0, icon: "↕" },
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">V</div>
          <div>
            <h2>Vehicle<span>IQ</span></h2>
            <p>ANALYTICS PLATFORM</p>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <a className="nav-item active" href="#dashboard"><span>▦</span> Dashboard</a>
        <a className="nav-item" href="#upload"><span>⇧</span> Video Processing</a>
        <a className="nav-item" href="#detections"><span>◎</span> Vehicle Detections</a>

        <div className="sidebar-bottom">
          <div className="system-status">
            <span className={`status-dot ${health === "Online" ? "green" : ""}`} />
            <div><strong>API Status</strong><p>{health}</p></div>
          </div>
          <p className="sidebar-version">VEHICLE ANALYTICS · v1.0</p>
        </div>
      </aside>

      <main className="main-content" id="dashboard">
        <header className="topbar">
          <div>
            <p className="eyebrow">INTELLIGENT TRAFFIC MONITORING</p>
            <h1>Vehicle Analytics Dashboard</h1>
            <p className="subtitle">Monitor traffic, process videos and analyze vehicle detections.</p>
          </div>
          <button className="refresh-button" onClick={loadDashboard}>↻ <span>Refresh Data</span></button>
        </header>

        <section className="welcome-banner">
          <div>
            <span className="banner-tag">AI-POWERED MONITORING</span>
            <h2>Traffic intelligence, at a glance.</h2>
            <p>Upload traffic footage to detect vehicles and generate analytics.</p>
            <a href="#upload" className="primary-button">Upload Traffic Video <span>→</span></a>
          </div>
          <div className="banner-art" aria-hidden="true">
            <div className="radar radar-one" />
            <div className="radar radar-two" />
            <div className="radar radar-three" />
            <div className="radar-center">V</div>
            <span className="radar-label">AI VISION</span>
          </div>
        </section>

        <section className="section-heading">
          <div><h2>Traffic Overview</h2><p>Vehicle metrics reported by the backend</p></div>
          <span className="live-badge"><span className="status-dot green" /> AUTO REFRESH · 5 SEC</span>
        </section>

        <section className="stats-grid">
          {cards.map((card, index) => (
            <article className="stat-card" key={card.label}>
              <div className={`stat-icon icon-${index}`}>{card.icon}</div>
              <p>{card.label}</p>
              <div className="stat-value">{card.value}</div>
              <span className="stat-caption">Backend reported value</span>
            </article>
          ))}
        </section>

        <section className="content-grid">
          <article className="panel upload-panel" id="upload">
            <div className="panel-heading">
              <div><h2>Process Traffic Video</h2><p>Upload a supported video for analysis.</p></div>
              <span className="panel-icon">⇧</span>
            </div>

            <form onSubmit={processVideo}>
              <label className="dropzone">
                <input
                  type="file"
                  accept=".mp4,.avi,.mov,.mkv,video/mp4,video/quicktime"
                  onChange={(event) => {
                    setFile(event.target.files?.[0] || null);
                    setMessage("");
                    setError("");
                    setOutputVideo("");
                  }}
                />
                <span className="upload-symbol">↑</span>
                <strong>{file ? file.name : "Choose a traffic video"}</strong>
                <span className="dropzone-help">
                  {file ? `${(file.size / (1024 * 1024)).toFixed(2)} MB selected` : "Click to browse · MP4, AVI, MOV or MKV"}
                </span>
              </label>

              <button className="submit-button" type="submit" disabled={loading || !file}>
                {loading ? "Processing video..." : "Start Video Processing →"}
              </button>
            </form>

            {loading && <div className="progress-box"><div className="progress-track"><div className="progress-indicator" /></div>Processing can take some time on a CPU.</div>}
            {message && <div className="message success">✓ {message}</div>}
            {error && <div className="message error">⚠ {error}</div>}

            {outputVideo && (
              <div className="output-box">
                <h3>Processed Video</h3>
                <video controls src={outputVideo} />
              </div>
            )}
          </article>

          <article className="panel detection-panel" id="detections">
            <div className="panel-heading">
              <div><h2>Recent Detections</h2><p>Detection records received from the API.</p></div>
              <span className="count-badge">{detections.length}</span>
            </div>

            {detections.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">◎</div>
                <h3>No detection records yet</h3>
                <p>Upload and process a video. Records appear here when the backend returns or stores detections.</p>
              </div>
            ) : (
              <div className="table-wrapper">
                <table>
                  <thead><tr><th>Vehicle</th><th>Confidence</th><th>Color</th><th>Track ID</th></tr></thead>
                  <tbody>
                    {detections.slice(0, 100).map((item, index) => (
                      <tr key={item.track_id ?? item.id ?? index}>
                        <td><span className="vehicle-name">{item.class_name || item.vehicle_type || item.label || "Vehicle"}</span></td>
                        <td>{typeof item.confidence === "number" ? `${(item.confidence * 100).toFixed(1)}%` : "—"}</td>
                        <td>{item.color || "—"}</td>
                        <td>{item.track_id ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </article>
        </section>

        <footer className="footer">
          <span>VehicleIQ · Vehicle Analytics System</span>
          <span>AI Vision · Traffic Monitoring · Analytics</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
