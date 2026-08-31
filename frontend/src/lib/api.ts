import { QueryResponse, DashboardResponse, SchemaResponse, UploadResponse, QueryResultData } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" && window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "http://localhost:8000");

function getWorkspaceId(): string {
  const key = "datadarshan-workspace-id";
  const existing = window.localStorage.getItem(key);
  if (existing) return existing;
  const created = crypto.randomUUID();
  window.localStorage.setItem(key, created);
  return created;
}

function getApiBase(): string {
  if (API_BASE.includes("your-backend-api-url")) {
    throw new Error("The backend API URL is not configured for this deployment.");
  }
  return API_BASE.replace(/\/$/, "");
}

async function fetchApi(path: string, init?: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 30_000);
  try {
    return await fetch(`${getApiBase()}${path}`, {
      ...init,
      headers: {
        ...(init?.headers || {}),
        "X-Workspace-ID": getWorkspaceId(),
      },
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("The backend request timed out. Please try again.");
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function fetchSchema(): Promise<SchemaResponse> {
  const res = await fetchApi("/api/schema", {
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
  previousContext?: QueryResultData
): Promise<QueryResponse> {
  const res = await fetchApi("/api/query", {
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
  const res = await fetchApi("/api/dashboard", {
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

export async function uploadCSVFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetchApi("/api/upload", {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `CSV upload failed (${res.status})`);
  }
  const data = await res.json();
  return data;
}
