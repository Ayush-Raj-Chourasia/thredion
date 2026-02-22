"use client";

import { useEffect, useState } from "react";
import { BarChart3, Loader2 } from "lucide-react";
import { cn, categoryColor, categoryDotColor } from "@/lib/utils";
import type { Stats, CategoryCount } from "@/lib/types";
import { getStats, getCategories } from "@/lib/api";

export default function StatsView({ refreshKey }: { refreshKey?: number }) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [categories, setCategories] = useState<CategoryCount[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getStats(), getCategories()])
      .then(([s, c]) => {
        setStats(s);
        setCategories(c);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [refreshKey]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-surface-400" />
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="rounded-2xl border border-dashed border-surface-300 dark:border-gray-700 bg-surface-50 dark:bg-gray-900 p-10 text-center">
        <BarChart3 className="mx-auto mb-3 h-10 w-10 text-surface-400 dark:text-gray-500" />
        <p className="text-sm font-medium text-surface-600 dark:text-gray-400">No stats available</p>
        <p className="mt-1 text-xs text-surface-400 dark:text-gray-500">Start saving memories to see analytics.</p>
      </div>
    );
  }

  const maxCatCount = Math.max(...categories.map((c) => c.count), 1);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-2">
        <BarChart3 className="h-5 w-5 text-brand-500" />
        <h2 className="text-base font-semibold text-surface-900 dark:text-white">Analytics</h2>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SummaryCard label="Total Memories" value={stats.total_memories} />
        <SummaryCard label="Connections" value={stats.total_connections} />
        <SummaryCard label="Resurfaced" value={stats.total_resurfaced} />
        <SummaryCard label="Avg Importance" value={stats.avg_importance} />
      </div>

      {/* Category distribution */}
      <div className="rounded-2xl border border-surface-300 dark:border-gray-700/50 bg-white dark:bg-gray-900 p-5">
        <h3 className="text-sm font-semibold text-surface-800 dark:text-gray-200 mb-4">Category Distribution</h3>
        {categories.length === 0 ? (
          <p className="text-sm text-surface-500 dark:text-gray-400">No categories yet.</p>
        ) : (
          <div className="space-y-3">
            {categories.map(({ category, count }) => (
              <div key={category} className="flex items-center gap-3">
                <span
                  className={cn(
                    "w-24 shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-medium text-center",
                    categoryColor(category)
                  )}
                >
                  {category}
                </span>
                <div className="flex-1 h-5 rounded-full bg-surface-100 dark:bg-gray-800 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${(count / maxCatCount) * 100}%`,
                      backgroundColor: categoryDotColor(category),
                    }}
                  />
                </div>
                <span className="text-sm font-semibold text-surface-700 dark:text-gray-300 w-8 text-right">
                  {count}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Top insights */}
      <div className="rounded-2xl border border-surface-300 dark:border-gray-700/50 bg-white dark:bg-gray-900 p-5">
        <h3 className="text-sm font-semibold text-surface-800 dark:text-gray-200 mb-3">Quick Insights</h3>
        <ul className="space-y-2 text-sm text-surface-600 dark:text-gray-400">
          <li>
            <span className="font-medium text-surface-800 dark:text-gray-200">Top category:</span>{" "}
            {stats.top_category}
          </li>
          <li>
            <span className="font-medium text-surface-800 dark:text-gray-200">Knowledge density:</span>{" "}
            {stats.total_connections > 0 && stats.total_memories > 0
              ? `${(stats.total_connections / stats.total_memories).toFixed(1)} connections per memory`
              : "No connections yet"}
          </li>
          <li>
            <span className="font-medium text-surface-800 dark:text-gray-200">Resurfacing rate:</span>{" "}
            {stats.total_resurfaced > 0 && stats.total_memories > 0
              ? `${((stats.total_resurfaced / stats.total_memories) * 100).toFixed(0)}% of memories resurfaced`
              : "No resurfacing yet"}
          </li>
        </ul>
      </div>
    </div>
  );
}

function SummaryCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-surface-300 dark:border-gray-700/50 bg-surface-50 dark:bg-gray-800 p-4 text-center">
      <span className="text-2xl font-bold text-surface-900 dark:text-white">{value}</span>
      <p className="mt-1 text-[11px] text-surface-500 dark:text-gray-400 uppercase tracking-wider font-medium">
        {label}
      </p>
    </div>
  );
}
