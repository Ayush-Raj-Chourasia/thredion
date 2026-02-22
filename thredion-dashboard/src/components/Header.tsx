"use client";

import { useState } from "react";
import {
  Brain,
  Search,
  Plus,
  Sparkles,
  BarChart3,
  Network,
  Lightbulb,
  X,
  LogOut,
  Phone,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface HeaderProps {
  searchQuery: string;
  onSearch: (query: string) => void;
  activeTab: string;
  onTabChange: (tab: string) => void;
  onAddUrl: (url: string) => void;
  isProcessing: boolean;
  userPhone?: string;
  onLogout?: () => void;
}

const TABS = [
  { id: "memories", label: "Memories", icon: Brain },
  { id: "insights", label: "Insights", icon: Lightbulb },
  { id: "graph", label: "Knowledge Graph", icon: Network },
  { id: "stats", label: "Stats", icon: BarChart3 },
];

export default function Header({
  searchQuery,
  onSearch,
  activeTab,
  onTabChange,
  onAddUrl,
  isProcessing,
  userPhone,
  onLogout,
}: HeaderProps) {
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [urlInput, setUrlInput] = useState("");

  const handleSubmitUrl = () => {
    const trimmed = urlInput.trim();
    if (!trimmed) return;
    onAddUrl(trimmed);
    setUrlInput("");
    setShowUrlInput(false);
  };

  return (
    <header className="sticky top-0 z-40 border-b border-surface-200 bg-white/80 backdrop-blur-xl">
      {/* Top bar */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <div className="flex h-16 items-center justify-between gap-4">
          {/* Logo */}
          <div className="flex items-center gap-2.5 shrink-0">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 shadow-md shadow-brand-200">
              <Brain className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-surface-900 tracking-tight leading-none">
                Thredion
              </h1>
              <p className="text-[10px] text-surface-500 font-medium tracking-widest uppercase leading-none mt-0.5">
                Cognitive Memory
              </p>
            </div>
          </div>

          {/* Search */}
          <div className="flex-1 max-w-md hidden sm:block">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-surface-400" />
              <input
                type="text"
                placeholder="Search memories, tags, topics…"
                value={searchQuery}
                onChange={(e) => onSearch(e.target.value)}
                className="w-full rounded-xl border border-surface-200 bg-surface-50 py-2 pl-10 pr-4 text-sm text-surface-800 placeholder-surface-400 transition-all focus:border-brand-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-100"
              />
              {searchQuery && (
                <button
                  onClick={() => onSearch("")}
                  aria-label="Clear search"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-600"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 shrink-0">
            {/* User indicator */}
            {userPhone && (
              <div className="hidden sm:flex items-center gap-1.5 text-xs text-surface-500 bg-surface-50 px-2.5 py-1.5 rounded-lg border border-surface-200">
                <Phone className="h-3 w-3" />
                <span>{userPhone}</span>
              </div>
            )}

            {showUrlInput ? (
              <div className="flex items-center gap-2">
                <input
                  type="url"
                  placeholder="Paste URL…"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSubmitUrl()}
                  className="w-56 rounded-lg border border-brand-300 bg-white px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200"
                  autoFocus
                />
                <button
                  onClick={handleSubmitUrl}
                  disabled={isProcessing || !urlInput.trim()}
                  className="rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50 transition-colors"
                >
                  {isProcessing ? "Processing…" : "Save"}
                </button>
                <button
                  onClick={() => { setShowUrlInput(false); setUrlInput(""); }}
                  aria-label="Cancel"
                  className="text-surface-400 hover:text-surface-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowUrlInput(true)}
                className="flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-md shadow-brand-200 hover:bg-brand-700 transition-all active:scale-95"
              >
                <Plus className="h-4 w-4" />
                <span className="hidden sm:inline">Add Memory</span>
              </button>
            )}

            {/* Logout */}
            {onLogout && (
              <button
                onClick={onLogout}
                title="Log out"
                className="flex items-center justify-center w-9 h-9 rounded-xl text-surface-400 hover:text-red-600 hover:bg-red-50 transition-all"
              >
                <LogOut className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tab bar */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <nav className="flex gap-1 -mb-px overflow-x-auto pb-px">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={cn(
                  "flex items-center gap-1.5 whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "border-brand-600 text-brand-700"
                    : "border-transparent text-surface-500 hover:border-surface-300 hover:text-surface-700"
                )}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Mobile search */}
      <div className="sm:hidden px-4 pb-3 pt-1">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-surface-400" />
          <input
            type="text"
            placeholder="Search…"
            value={searchQuery}
            onChange={(e) => onSearch(e.target.value)}
            className="w-full rounded-xl border border-surface-200 bg-surface-50 py-2 pl-10 pr-4 text-sm placeholder-surface-400 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
          />
        </div>
      </div>
    </header>
  );
}
