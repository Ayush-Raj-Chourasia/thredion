/* ── Thredion Dashboard — API Client ────────────────────── */

import type {
  Memory,
  ResurfacedMemory,
  KnowledgeGraph,
  Stats,
  CategoryCount,
  ProcessResult,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ── Auth token management ─────────────────────────────── */

let _authToken: string | null = null;

export function setAuthToken(token: string | null) {
  _authToken = token;
  if (token) {
    if (typeof window !== "undefined") localStorage.setItem("thredion_token", token);
  } else {
    if (typeof window !== "undefined") localStorage.removeItem("thredion_token");
  }
}

export function getAuthToken(): string | null {
  if (_authToken) return _authToken;
  if (typeof window !== "undefined") {
    _authToken = localStorage.getItem("thredion_token");
  }
  return _authToken;
}

export function clearAuth() {
  _authToken = null;
  if (typeof window !== "undefined") {
    localStorage.removeItem("thredion_token");
    localStorage.removeItem("thredion_user");
  }
}

/* ── Core fetch wrapper ────────────────────────────────── */

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const controller = new AbortController();
  const timeoutMs = options?.method === "POST" ? 60_000 : 15_000;
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  const token = getAuthToken();
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(options?.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers,
    });
    if (res.status === 401) {
      // Don't clear auth for pre-auth endpoints (login flow)
      const isAuthEndpoint = path.startsWith("/auth/send-otp") || path.startsWith("/auth/verify-otp");
      if (!isAuthEndpoint) {
        clearAuth();
        if (typeof window !== "undefined") window.location.reload();
      }
      throw new Error("Session expired. Please log in again.");
    }
    if (!res.ok) {
      const text = await res.text().catch(() => "Unknown error");
      throw new Error(`API ${res.status}: ${text}`);
    }
    return res.json();
  } catch (err: any) {
    if (err.name === "AbortError") {
      throw new Error("Request timed out. The server may still be loading the AI model — try again in a few seconds.");
    }
    // Only treat as network error if it's a genuine fetch failure,
    // NOT an API error response we already parsed above (those start with "API ")
    if (
      !err.message?.startsWith("API ") &&
      !err.message?.startsWith("Session expired") &&
      (err.name === "TypeError" || err.message?.includes("fetch"))
    ) {
      console.warn(`[Thredion API] Backend unreachable at ${url}.`);
      throw new Error("Backend unreachable. Make sure thredion-engine is running on port 8000.");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

/* ── Auth ──────────────────────────────────────────────── */

export async function sendOTP(phone: string): Promise<{ detail: string; expires_in_seconds: number }> {
  const qs = new URLSearchParams({ phone });
  return apiFetch(`/auth/send-otp?${qs}`, { method: "POST" });
}

export async function verifyOTP(phone: string, code: string): Promise<{ token: string; user: any }> {
  const qs = new URLSearchParams({ phone, code });
  return apiFetch(`/auth/verify-otp?${qs}`, { method: "POST" });
}

export async function getMe(): Promise<any> {
  return apiFetch("/auth/me");
}

/* ── Memories ──────────────────────────────────────────── */

export async function getMemories(params?: {
  search?: string;
  category?: string;
  sort?: string;
  limit?: number;
}): Promise<Memory[]> {
  const qs = new URLSearchParams();
  if (params?.search) qs.set("search", params.search);
  if (params?.category) qs.set("category", params.category);
  if (params?.sort) qs.set("sort", params.sort);
  if (params?.limit) qs.set("limit", String(params.limit));
  const query = qs.toString();
  return apiFetch<Memory[]>(`/api/memories${query ? `?${query}` : ""}`);
}

export async function getMemory(id: string): Promise<Memory> {
  return apiFetch<Memory>(`/api/memories/${id}`);
}

export async function deleteMemory(id: string): Promise<void> {
  await apiFetch(`/api/memories/${id}`, { method: "DELETE" });
}

export async function processUrl(url: string): Promise<ProcessResult> {
  const qs = new URLSearchParams({ url });
  return apiFetch<ProcessResult>(`/api/process?${qs}`, { method: "POST" });
}

/* ── Knowledge Graph ───────────────────────────────────── */

export async function getGraph(): Promise<KnowledgeGraph> {
  return apiFetch<KnowledgeGraph>("/api/graph");
}

/* ── Resurfaced ────────────────────────────────────────── */

export async function getResurfaced(limit = 20): Promise<ResurfacedMemory[]> {
  return apiFetch<ResurfacedMemory[]>(`/api/resurfaced?limit=${limit}`);
}

/* ── Stats ─────────────────────────────────────────────── */

export async function getStats(): Promise<Stats> {
  return apiFetch<Stats>("/api/stats");
}

/* ── Categories ────────────────────────────────────────── */

export async function getCategories(): Promise<CategoryCount[]> {
  return apiFetch<CategoryCount[]>("/api/categories");
}

/* ── Random Inspiration ────────────────────────────────── */

export async function getRandomMemory(): Promise<Memory> {
  return apiFetch<Memory>("/api/random");
}
