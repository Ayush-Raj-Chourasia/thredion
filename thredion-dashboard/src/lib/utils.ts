/* ── Thredion Dashboard — Utility helpers ──────────────── */

import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/* ── Category → Color mapping ─────────────────────────── */

const CATEGORY_COLORS: Record<string, string> = {
  Fitness: "bg-emerald-100 text-emerald-800 border-emerald-200",
  Coding: "bg-violet-100 text-violet-800 border-violet-200",
  Design: "bg-pink-100 text-pink-800 border-pink-200",
  Food: "bg-amber-100 text-amber-800 border-amber-200",
  Travel: "bg-sky-100 text-sky-800 border-sky-200",
  Business: "bg-slate-100 text-slate-800 border-slate-200",
  Science: "bg-teal-100 text-teal-800 border-teal-200",
  Music: "bg-rose-100 text-rose-800 border-rose-200",
  Art: "bg-fuchsia-100 text-fuchsia-800 border-fuchsia-200",
  Fashion: "bg-orange-100 text-orange-800 border-orange-200",
  Education: "bg-indigo-100 text-indigo-800 border-indigo-200",
  Technology: "bg-cyan-100 text-cyan-800 border-cyan-200",
  Health: "bg-green-100 text-green-800 border-green-200",
  Finance: "bg-yellow-100 text-yellow-800 border-yellow-200",
  Motivation: "bg-red-100 text-red-800 border-red-200",
  Entertainment: "bg-purple-100 text-purple-800 border-purple-200",
  Sports: "bg-lime-100 text-lime-800 border-lime-200",
  Lifestyle: "bg-stone-100 text-stone-800 border-stone-200",
  DIY: "bg-zinc-100 text-zinc-800 border-zinc-200",
  Photography: "bg-blue-100 text-blue-800 border-blue-200",
};

export function categoryColor(category: string): string {
  return CATEGORY_COLORS[category] || "bg-gray-100 text-gray-700 border-gray-200";
}

/* ── Category → Dot color for graphs ──────────────────── */

const CATEGORY_DOT: Record<string, string> = {
  Fitness: "#10b981",
  Coding: "#8b5cf6",
  Design: "#ec4899",
  Food: "#f59e0b",
  Travel: "#0ea5e9",
  Business: "#64748b",
  Science: "#14b8a6",
  Music: "#f43f5e",
  Technology: "#06b6d4",
  Education: "#6366f1",
  Health: "#22c55e",
  Finance: "#eab308",
  Motivation: "#ef4444",
  Art: "#d946ef",
  Fashion: "#f97316",
  Entertainment: "#a855f7",
  Sports: "#84cc16",
  Lifestyle: "#78716c",
  DIY: "#71717a",
  Photography: "#3b82f6",
};

export function categoryDotColor(category: string): string {
  return CATEGORY_DOT[category] || "#9ca3af";
}

/* ── Platform → Icon name mapping ─────────────────────── */

export function platformIcon(platform: string): string {
  const map: Record<string, string> = {
    instagram: "Instagram",
    twitter: "Twitter",
    youtube: "Youtube",
    reddit: "MessageSquare",
    tiktok: "Play",
    article: "FileText",
  };
  return map[platform] || "Link";
}

/* ── Platform → Display name ──────────────────────────── */

export function platformName(platform: string): string {
  const map: Record<string, string> = {
    instagram: "Instagram",
    twitter: "Twitter / X",
    youtube: "YouTube",
    reddit: "Reddit",
    tiktok: "TikTok",
    article: "Article",
  };
  return map[platform] || "Link";
}

/* ── Importance → Visual bar ──────────────────────────── */

export function importanceLevel(score: number): {
  label: string;
  color: string;
  bgColor: string;
} {
  if (score >= 80) return { label: "Critical", color: "text-red-600", bgColor: "bg-red-500" };
  if (score >= 60) return { label: "High", color: "text-orange-600", bgColor: "bg-orange-500" };
  if (score >= 40) return { label: "Medium", color: "text-yellow-600", bgColor: "bg-yellow-500" };
  return { label: "Low", color: "text-green-600", bgColor: "bg-green-500" };
}

/* ── Time ago ─────────────────────────────────────────── */

export function timeAgo(dateStr: string): string {
  if (!dateStr) return "";
  const now = new Date();
  const date = new Date(dateStr);
  const diff = now.getTime() - date.getTime();

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 30) return `${Math.floor(days / 30)}mo ago`;
  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return "just now";
}

/* ── Truncate text ────────────────────────────────────── */

export function truncate(text: string, maxLength: number): string {
  if (!text) return "";
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trimEnd() + "…";
}
