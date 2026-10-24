export default function StatCard({ title, value, detail }) {
  return <div className="stat-card"><div>{title}</div><h2>{value}</h2><small>{detail}</small></div>
}
