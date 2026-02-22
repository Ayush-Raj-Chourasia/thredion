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

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const controller = new AbortController();
  const timeoutMs = options?.method === "POST" ? 60_000 : 15_000;
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        ...options?.headers,
      },
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "Unknown error");
      throw new Error(`API ${res.status}: ${text}`);
    }
    return res.json();
  } catch (err: any) {
    if (err.name === "AbortError") {
      throw new Error("Request timed out. The server may still be loading the AI model — try again in a few seconds.");
    }
    // Network error — provide helpful fallback
    if (err.name === "TypeError" || err.message?.includes("fetch") || err.message?.includes("Failed")) {
      console.warn(`[Thredion API] Backend unreachable at ${url}.`);
      throw new Error("Backend unreachable. Make sure thredion-engine is running on port 8000.");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
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

export async function getMemory(id: number): Promise<Memory> {
  return apiFetch<Memory>(`/api/memories/${id}`);
}

export async function deleteMemory(id: number): Promise<void> {
  await apiFetch(`/api/memories/${id}`, { method: "DELETE" });
}

export async function processUrl(
  url: string,
  userPhone = "dashboard"
): Promise<ProcessResult> {
  const qs = new URLSearchParams({ url, user_phone: userPhone });
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
