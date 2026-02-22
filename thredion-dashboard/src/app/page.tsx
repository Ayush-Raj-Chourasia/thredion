"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { Loader2, AlertCircle, Brain } from "lucide-react";

import Header from "@/components/Header";
import StatsBar from "@/components/StatsBar";
import CategoryFilter from "@/components/CategoryFilter";
import MemoryCard from "@/components/MemoryCard";
import ResurfacedPanel from "@/components/ResurfacedPanel";
import KnowledgeGraphView from "@/components/KnowledgeGraphView";
import StatsView from "@/components/StatsView";
import InspireModal from "@/components/InspireModal";

import {
  getMemories,
  getCategories,
  getResurfaced,
  processUrl,
  deleteMemory as apiDeleteMemory,
} from "@/lib/api";
import type { Memory, CategoryCount, ResurfacedMemory } from "@/lib/types";

export default function Home() {
  // ── State ─────────────────────────────────────────────
  const [memories, setMemories] = useState<Memory[]>([]);
  const [categories, setCategories] = useState<CategoryCount[]>([]);
  const [resurfaced, setResurfaced] = useState<ResurfacedMemory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [activeTab, setActiveTab] = useState("memories");
  const [isProcessing, setIsProcessing] = useState(false);
  const [inspireMemory, setInspireMemory] = useState<Memory | null>(null);
  const [sortMode, setSortMode] = useState<"newest" | "oldest" | "importance">("newest");

  // Debounce search
  const searchTimeout = useRef<NodeJS.Timeout | null>(null);
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => {
      if (searchTimeout.current) clearTimeout(searchTimeout.current);
    };
  }, [searchQuery]);

  // ── Data fetching ─────────────────────────────────────
  const fetchAll = useCallback(async () => {
    try {
      setError(null);
      const [mems, cats, res] = await Promise.all([
        getMemories({
          search: debouncedSearch,
          category: selectedCategory,
          sort: sortMode,
        }),
        getCategories(),
        getResurfaced(),
      ]);
      setMemories(mems);
      setCategories(cats);
      setResurfaced(res);
    } catch (err: any) {
      setError(err.message || "Failed to fetch data");
      // Set empty arrays to prevent crashes
      setMemories([]);
      setCategories([]);
      setResurfaced([]);
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, selectedCategory, sortMode]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  // ── Handlers ──────────────────────────────────────────
  const handleAddUrl = async (url: string) => {
    setIsProcessing(true);
    setError(null);
    try {
      const result = await processUrl(url);
      if (result?.duplicate) {
        setInfo("This link is already in your memory vault!");
      }
      await fetchAll(); // Refresh everything
    } catch (err: any) {
      setError(err.message || "Failed to process URL");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await apiDeleteMemory(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
    } catch (err: any) {
      setError(err.message || "Failed to delete memory");
    }
  };

  // ── Render ────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-surface-50">
      <Header
        searchQuery={searchQuery}
        onSearch={setSearchQuery}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onAddUrl={handleAddUrl}
        isProcessing={isProcessing}
      />

      <main className="mx-auto max-w-7xl px-4 sm:px-6 py-6 space-y-6">
        {/* Error banner */}
        {error && (
          <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 animate-fade-in">
            <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
            <p className="flex-1">{error}</p>
            <button
              onClick={() => setError(null)}
              className="text-red-400 hover:text-red-600 text-xs font-medium"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Info banner */}
        {info && (
          <div className="flex items-center gap-3 rounded-xl border border-brand-200 bg-brand-50 p-4 text-sm text-brand-700 animate-fade-in">
            <Brain className="h-5 w-5 shrink-0 text-brand-500" />
            <p className="flex-1">{info}</p>
            <button
              onClick={() => setInfo(null)}
              className="text-brand-400 hover:text-brand-600 text-xs font-medium"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Processing indicator */}
        {isProcessing && (
          <div className="flex items-center gap-3 rounded-xl border border-brand-200 bg-brand-50 p-4 text-sm text-brand-700 animate-pulse-soft">
            <Loader2 className="h-5 w-5 animate-spin text-brand-500" />
            <p>
              Processing URL through cognitive pipeline — extracting, embedding,
              classifying, connecting…
            </p>
          </div>
        )}

        {/* ── Tab: Memories ───────────────────────────── */}
        {activeTab === "memories" && (
          <>
            <StatsBar onInspire={setInspireMemory} />

            {/* Sort + Category filters */}
            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
              <div className="flex items-center gap-2">
                <label className="text-xs text-surface-500 font-medium">Sort:</label>
                <select
                  value={sortMode}
                  aria-label="Sort memories"
                  onChange={(e) => setSortMode(e.target.value as any)}
                  className="rounded-lg border border-surface-200 bg-white px-2.5 py-1.5 text-xs text-surface-700 focus:border-brand-400 focus:outline-none"
                >
                  <option value="newest">Newest first</option>
                  <option value="oldest">Oldest first</option>
                  <option value="importance">Importance</option>
                </select>
              </div>
              <div className="flex-1">
                <CategoryFilter
                  categories={categories}
                  selected={selectedCategory}
                  onSelect={setSelectedCategory}
                />
              </div>
            </div>

            {/* Memories grid */}
            {loading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="h-8 w-8 animate-spin text-surface-400" />
              </div>
            ) : memories.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-center animate-fade-in">
                <Brain className="h-16 w-16 text-surface-300 mb-4" />
                <h3 className="text-lg font-semibold text-surface-700 mb-1">
                  {debouncedSearch || selectedCategory
                    ? "No matches found"
                    : "No memories yet"}
                </h3>
                <p className="text-sm text-surface-500 max-w-md">
                  {debouncedSearch || selectedCategory
                    ? "Try widening your search or clearing the filter."
                    : "Send a link via WhatsApp or use the \"Add Memory\" button above to start building your cognitive memory."}
                </p>
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {memories.map((m) => (
                  <MemoryCard key={m.id} memory={m} onDelete={handleDelete} />
                ))}
              </div>
            )}
          </>
        )}

        {/* ── Tab: Insights ───────────────────────────── */}
        {activeTab === "insights" && (
          <ResurfacedPanel items={resurfaced} />
        )}

        {/* ── Tab: Knowledge Graph ────────────────────── */}
        {activeTab === "graph" && <KnowledgeGraphView />}

        {/* ── Tab: Stats ──────────────────────────────── */}
        {activeTab === "stats" && <StatsView />}
      </main>

      {/* Random Inspiration Modal */}
      <InspireModal
        memory={inspireMemory}
        onClose={() => setInspireMemory(null)}
      />

      {/* Footer */}
      <footer className="mt-12 border-t border-surface-200 bg-white py-6">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 text-center">
          <p className="text-xs text-surface-500">
            <span className="font-semibold text-surface-700">Thredion</span> — AI
            Cognitive Memory Engine · Built for{" "}
            <span className="font-medium">Hack The Thread</span>
          </p>
        </div>
      </footer>
    </div>
  );
}
