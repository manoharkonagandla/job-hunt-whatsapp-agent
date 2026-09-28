const STATUS_COLORS = {
  applied: "#6b7fd7",
  interviewing: "#e8a33d",
  offer: "#3fb27f",
  rejected: "#d9534f",
  withdrawn: "#9a9a9a",
};

export default function StatsBar({ applications }) {
  const counts = applications.reduce((acc, app) => {
    acc[app.status] = (acc[app.status] || 0) + 1;
    return acc;
  }, {});

  const statuses = ["applied", "interviewing", "offer", "rejected", "withdrawn"];

  return (
    <div className="stats-bar">
      <div className="stat stat-total">
        <span className="stat-count">{applications.length}</span>
        <span className="stat-label">Total</span>
      </div>
      {statuses.map((status) => (
        <div className="stat" key={status}>
          <span
            className="stat-count"
            style={{ color: STATUS_COLORS[status] }}
          >
            {counts[status] || 0}
          </span>
          <span className="stat-label">{status}</span>
        </div>
      ))}
    </div>
  );
}

export { STATUS_COLORS };
