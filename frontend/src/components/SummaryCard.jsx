export default function SummaryCard({ label, value }) {
  return (
    <div className="summary-card">
      <p className="summary-label">{label}</p>
      <h3>{value}</h3>
    </div>
  );
}
