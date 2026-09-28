const STATUSES = ["all", "applied", "interviewing", "offer", "rejected", "withdrawn"];

export default function StatusFilter({ active, onChange }) {
  return (
    <div className="status-filter">
      {STATUSES.map((status) => (
        <button
          key={status}
          className={`filter-btn ${active === status ? "active" : ""}`}
          onClick={() => onChange(status)}
        >
          {status}
        </button>
      ))}
    </div>
  );
}
