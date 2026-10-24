export default function VehicleTable({ detections = [] }) {
  return <table><thead><tr><th>Time</th><th>Vehicle</th><th>Color</th><th>Confidence</th></tr></thead>
    <tbody>{detections.map(item => <tr key={item.id}><td>{item.timestamp}</td><td>{item.vehicle_type}</td><td>{item.color}</td><td>{Math.round(item.confidence * 100)}%</td></tr>)}</tbody>
  </table>
}
