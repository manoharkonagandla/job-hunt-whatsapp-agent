import { useState, useEffect, useMemo, useCallback } from "react";
import { getApplications, addApplication, updateApplication, setToken } from "./api/client";
import StatsBar from "./components/StatsBar";
import StatusChart from "./components/StatusChart";
import StatusFilter from "./components/StatusFilter";
import ApplicationCard from "./components/ApplicationCard";
import AddApplicationForm from "./components/AddApplicationForm";
import TokenPrompt from "./components/TokenPrompt";
import "./App.css";

export default function App() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");

  const loadApplications = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getApplications();
      setApplications(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadApplications();
  }, [loadApplications]);

  const filtered = useMemo(() => {
    if (filter === "all") return applications;
    return applications.filter((app) => app.status === filter);
  }, [applications, filter]);

  async function handleAdd(data) {
    const created = await addApplication(data);
    setApplications((prev) => [created, ...prev]);
  }

  async function handleStatusChange(id, status) {
    const updated = await updateApplication(id, { status });
    setApplications((prev) => prev.map((a) => (a.id === id ? updated : a)));
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Job Hunt Dashboard</h1>
        <p className="app-subtitle">
          The web view for the WhatsApp agent — same data, different lens.
        </p>
      </header>

      {error?.status === 401 && (
        <TokenPrompt
          onSubmit={(t) => {
            setToken(t);
            loadApplications();
          }}
        />
      )}

      {error && (
        <div className="banner-error">
          {error.status === 401
            ? error.message
            : `Couldn't reach the backend (${error.message}). Is it running?`}
        </div>
      )}

      {!error && (
        <>
          <StatsBar applications={applications} />
          <StatusChart applications={applications} />

          <div className="toolbar">
            <StatusFilter active={filter} onChange={setFilter} />
            <AddApplicationForm onAdd={handleAdd} />
          </div>

          {loading ? (
            <div className="loading">Loading…</div>
          ) : filtered.length === 0 ? (
            <div className="empty-state">Nothing here yet.</div>
          ) : (
            <div className="app-list">
              {filtered.map((app) => (
                <ApplicationCard
                  key={app.id}
                  app={app}
                  onStatusChange={handleStatusChange}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
