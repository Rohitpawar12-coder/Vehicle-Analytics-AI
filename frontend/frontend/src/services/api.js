const API = 'http://127.0.0.1:8000'
export async function getStats() {
  const response = await fetch(`${API}/api/stats`)
  if (!response.ok) throw new Error('Could not load stats')
  return response.json()
}
export async function getDetections() {
  const response = await fetch(`${API}/api/detections`)
  if (!response.ok) throw new Error('Could not load detections')
  return response.json()
}
