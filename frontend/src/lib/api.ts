import { QueryResponse, DashboardResponse, SchemaResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchSchema(): Promise<SchemaResponse> {
  const res = await fetch(`${API_BASE}/api/schema`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch dataset schema: ${res.statusText}`);
  }
  return res.json();
}

export async function postQuery(
  query: string,
  previousContext?: Record<string, any>
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      previous_context: previousContext || null,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Query failed (${res.status})`);
  }
  return res.json();
}

export async function postDashboardQuery(
  query: string = "generate full dashboard overview"
): Promise<DashboardResponse> {
  const res = await fetch(`${API_BASE}/api/dashboard`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Dashboard generation failed (${res.status})`);
  }
  return res.json();
}

export async function uploadCSVFile(file: File): Promise<SchemaResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `CSV upload failed (${res.status})`);
  }
  const data = await res.json();
  return {
    profile: data.profile,
    suggested_questions: data.suggested_questions,
  };
}
