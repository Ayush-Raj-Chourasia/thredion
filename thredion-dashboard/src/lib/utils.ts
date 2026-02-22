/* ── Thredion Dashboard — Utility helpers ──────────────── */

import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/* ── Category → Color mapping ─────────────────────────── */

const CATEGORY_COLORS: Record<string, string> = {
  Fitness: "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-700/50",
  Coding: "bg-violet-100 text-violet-800 border-violet-300 dark:bg-violet-900/30 dark:text-violet-300 dark:border-violet-700/50",
  Design: "bg-pink-100 text-pink-800 border-pink-300 dark:bg-pink-900/30 dark:text-pink-300 dark:border-pink-700/50",
  Food: "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-700/50",
  Travel: "bg-sky-100 text-sky-800 border-sky-300 dark:bg-sky-900/30 dark:text-sky-300 dark:border-sky-700/50",
  Business: "bg-slate-100 text-slate-800 border-slate-300 dark:bg-slate-900/30 dark:text-slate-300 dark:border-slate-700/50",
  Science: "bg-teal-100 text-teal-800 border-teal-300 dark:bg-teal-900/30 dark:text-teal-300 dark:border-teal-700/50",
  Music: "bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-900/30 dark:text-rose-300 dark:border-rose-700/50",
  Art: "bg-fuchsia-100 text-fuchsia-800 border-fuchsia-300 dark:bg-fuchsia-900/30 dark:text-fuchsia-300 dark:border-fuchsia-700/50",
  Fashion: "bg-orange-100 text-orange-800 border-orange-300 dark:bg-orange-900/30 dark:text-orange-300 dark:border-orange-700/50",
  Education: "bg-indigo-100 text-indigo-800 border-indigo-300 dark:bg-indigo-900/30 dark:text-indigo-300 dark:border-indigo-700/50",
  Technology: "bg-cyan-100 text-cyan-800 border-cyan-300 dark:bg-cyan-900/30 dark:text-cyan-300 dark:border-cyan-700/50",
  Health: "bg-green-100 text-green-800 border-green-300 dark:bg-green-900/30 dark:text-green-300 dark:border-green-700/50",
  Finance: "bg-yellow-100 text-yellow-800 border-yellow-300 dark:bg-yellow-900/30 dark:text-yellow-300 dark:border-yellow-700/50",
  Motivation: "bg-red-100 text-red-800 border-red-300 dark:bg-red-900/30 dark:text-red-300 dark:border-red-700/50",
  Entertainment: "bg-purple-100 text-purple-800 border-purple-300 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-700/50",
  Sports: "bg-lime-100 text-lime-800 border-lime-300 dark:bg-lime-900/30 dark:text-lime-300 dark:border-lime-700/50",
  Lifestyle: "bg-stone-100 text-stone-800 border-stone-300 dark:bg-stone-900/30 dark:text-stone-300 dark:border-stone-700/50",
  DIY: "bg-zinc-100 text-zinc-800 border-zinc-300 dark:bg-zinc-900/30 dark:text-zinc-300 dark:border-zinc-700/50",
  Photography: "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-700/50",
};

export function categoryColor(category: string): string {
  return CATEGORY_COLORS[category] || "bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-800/50 dark:text-gray-300 dark:border-gray-700/50";
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
  if (score >= 80) return { label: "Critical", color: "text-red-600 dark:text-red-400", bgColor: "bg-red-500" };
  if (score >= 60) return { label: "High", color: "text-orange-600 dark:text-orange-400", bgColor: "bg-orange-500" };
  if (score >= 40) return { label: "Medium", color: "text-yellow-600 dark:text-yellow-400", bgColor: "bg-yellow-500" };
  return { label: "Low", color: "text-green-600 dark:text-green-400", bgColor: "bg-green-500" };
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

/* ── Format date ──────────────────────────────────────── */

export function formatDate(dateStr: string): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

/* ── Truncate text ────────────────────────────────────── */

export function truncate(text: string, maxLength: number): string {
  if (!text) return "";
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trimEnd() + "…";
}
