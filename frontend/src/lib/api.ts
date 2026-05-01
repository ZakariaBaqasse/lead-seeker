import { env } from "$env/dynamic/private";
const { BACKEND_URL, API_SECRET_KEY } = env;
import type {
  Lead,
  LeadsResponse,
  StatsResponse,
  PipelineStatus,
  RegenerateEmailResponse,
  LeadFilters,
  LeadUpdate,
} from "./types";

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function getHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
    "X-API-Key": API_SECRET_KEY,
  };
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const baseUrl = BACKEND_URL || "http://localhost:8000";
  const url = `${baseUrl}${path}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      ...getHeaders(),
      ...(options?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "Unknown error");
    throw new ApiError(
      `API error ${response.status}: ${text}`,
      response.status,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function getLeads(
  filters: LeadFilters = {},
): Promise<LeadsResponse> {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.region) params.set("region", filters.region);
  if (filters.from) params.set("from", filters.from);
  if (filters.to) params.set("to", filters.to);
  if (filters.search) params.set("search", filters.search);
  if (filters.page) params.set("page", String(filters.page));
  if (filters.limit) params.set("limit", String(filters.limit));
  if (filters.sort_by) params.set("sort_by", filters.sort_by);
  if (filters.sort_dir) params.set("sort_dir", filters.sort_dir);

  const query = params.toString();
  return apiFetch<LeadsResponse>(`/api/leads${query ? `?${query}` : ""}`);
}

export async function getLead(id: string): Promise<Lead> {
  return apiFetch<Lead>(`/api/leads/${id}`);
}

export async function updateLead(id: string, data: LeadUpdate): Promise<Lead> {
  return apiFetch<Lead>(`/api/leads/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteLead(id: string): Promise<void> {
  return apiFetch<void>(`/api/leads/${id}`, { method: "DELETE" });
}

export async function regenerateEmail(
  id: string,
): Promise<RegenerateEmailResponse> {
  return apiFetch<RegenerateEmailResponse>(`/api/leads/${id}/regenerate`, {
    method: "POST",
  });
}

export async function markFollowUpSent(id: string): Promise<Lead> {
  return apiFetch<Lead>(`/api/leads/${id}/follow-ups/mark-sent`, {
    method: "POST",
  });
}

export async function getStats(): Promise<StatsResponse> {
  return apiFetch<StatsResponse>("/api/stats");
}

export async function getPipelineStatus(): Promise<PipelineStatus> {
  return apiFetch<PipelineStatus>("/api/pipeline/status");
}

export async function runPipeline(): Promise<void> {
  return apiFetch<void>("/api/pipeline/run", { method: "POST" });
}

export { ApiError };
