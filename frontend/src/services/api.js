
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function apiFetch(endpoint, options = {}) {
  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    }
  );

  if (!response.ok) {
    const text = await response.text();

    throw new Error(
      `API ${response.status}: ${text || response.statusText}`
    );
  }

  return response.json();
}

export async function getDashboardOverview() {
  return apiFetch("/api/dashboard/overview");
}

export async function getAuditSummary() {
  return apiFetch("/api/audit/summary");
}

export async function getRedistributions() {
  return apiFetch("/api/redistribution");
}

export async function getInventory() {
  return apiFetch("/api/inventory");
}

export async function getMedicines() {
  return apiFetch("/api/medicines");
}

export async function getStockRisk() {
  return apiFetch("/api/ml/stock-risk");
}

export async function getAnomalies() {
  return apiFetch("/api/ml/anomalies");
}