import { useState } from "react";

export default function AddApplicationForm({ onAdd }) {
  const [open, setOpen] = useState(false);
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!company.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await onAdd({ company: company.trim(), role: role.trim() || null, status: "applied" });
      setCompany("");
      setRole("");
      setOpen(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (!open) {
    return (
      <button className="add-btn" onClick={() => setOpen(true)}>
        + Log an application
      </button>
    );
  }

  return (
    <form className="add-form" onSubmit={handleSubmit}>
      <input
        placeholder="Company"
        value={company}
        onChange={(e) => setCompany(e.target.value)}
        autoFocus
      />
      <input
        placeholder="Role (optional)"
        value={role}
        onChange={(e) => setRole(e.target.value)}
      />
      <div className="add-form-actions">
        <button type="submit" disabled={submitting || !company.trim()}>
          {submitting ? "Saving…" : "Save"}
        </button>
        <button type="button" onClick={() => setOpen(false)} className="secondary">
          Cancel
        </button>
      </div>
      {error && <div className="form-error">{error}</div>}
    </form>
  );
}
