// In dev the API runs on :8000. In production the FastAPI server also serves
// this app, so relative URLs ("") hit the same origin.
const BASE_URL =
  import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? "http://localhost:8000" : "");

const TOKEN_KEY = "jobhunt_api_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY) || "";
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t);

async function request(path, options = {}) {
  const token = getToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "X-API-Key": token } : {}),
    },
  });
  if (!res.ok) {
    const err = new Error(
      res.status === 401 ? "Unauthorized — enter your dashboard token." : `API error ${res.status}`
    );
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export const getApplications = () => request("/api/applications");

export const addApplication = (data) =>
  request("/api/applications", { method: "POST", body: JSON.stringify(data) });

export const updateApplication = (id, data) =>
  request(`/api/applications/${id}`, { method: "PATCH", body: JSON.stringify(data) });
