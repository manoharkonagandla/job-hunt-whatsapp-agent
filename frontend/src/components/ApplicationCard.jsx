import { useState } from "react";
import { STATUS_COLORS } from "./StatsBar";

const STATUS_OPTIONS = ["applied", "interviewing", "offer", "rejected", "withdrawn"];

function daysSince(dateStr) {
  const utc = /Z|[+-]\d\d:?\d\d$/.test(dateStr) ? dateStr : dateStr + "Z";
  const diffMs = Date.now() - new Date(utc).getTime();
  return Math.floor(diffMs / (1000 * 60 * 60 * 24));
}

export default function ApplicationCard({ app, onStatusChange }) {
  const [saving, setSaving] = useState(false);

  async function handleStatusChange(e) {
    const newStatus = e.target.value;
    setSaving(true);
    try {
      await onStatusChange(app.id, newStatus);
    } finally {
      setSaving(false);
    }
  }

  const stale = app.status === "applied" && daysSince(app.applied_on) >= 7;

  return (
    <div className={`app-card ${stale ? "stale" : ""}`}>
      <div className="app-card-main">
        <div className="app-card-company">{app.company}</div>
        <div className="app-card-role">{app.role || "Role not specified"}</div>
        <div className="app-card-meta">
          Applied {daysSince(app.applied_on)} day{daysSince(app.applied_on) === 1 ? "" : "s"} ago
          {stale && <span className="stale-badge">Follow up?</span>}
        </div>
      </div>
      <select
        className="status-select"
        value={app.status}
        onChange={handleStatusChange}
        disabled={saving}
        style={{ borderColor: STATUS_COLORS[app.status] }}
      >
        {STATUS_OPTIONS.map((s) => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>
    </div>
  );
}
