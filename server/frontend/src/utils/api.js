import { API } from "../App";

export function getAuthHeaders() {
  const token = localStorage.getItem("miner_dashboard_token");
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

export async function apiFetch(url, options = {}) {
  const headers = { ...getAuthHeaders(), ...options.headers };
  const r = await fetch(`${API}${url}`, { ...options, headers });
  return r;
}
