"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Brain,
  Link2,
  Lightbulb,
  BarChart3,
  TrendingUp,
  Shuffle,
  Loader2,
} from "lucide-react";
import { cn, categoryColor, importanceLevel } from "@/lib/utils";
import type { Stats, Memory } from "@/lib/types";
import { getStats, getRandomMemory } from "@/lib/api";

interface StatsBarProps {
  onInspire?: (memory: Memory) => void;
  refreshKey?: number;
}

export default function StatsBar({ onInspire, refreshKey }: StatsBarProps) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [inspiring, setInspiring] = useState(false);

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, [refreshKey]);

  const handleInspire = useCallback(async () => {
    setInspiring(true);
    try {
      const memory = await getRandomMemory();
      onInspire?.(memory);
    } catch {
      /* no memories yet */
    } finally {
      setInspiring(false);
    }
  }, [onInspire]);

  if (loading) {
    return (
      <div className="flex justify-center py-4">
        <Loader2 className="h-5 w-5 animate-spin text-surface-400" />
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="rounded-2xl border border-dashed border-surface-300 dark:border-gray-700 bg-surface-50 dark:bg-gray-900 p-6 text-center">
        <Brain className="mx-auto mb-2 h-8 w-8 text-surface-400 dark:text-gray-500" />
        <p className="text-sm text-surface-500 dark:text-gray-400">
          Backend offline — start thredion-engine to see stats.
        </p>
      </div>
    );
  }

  const imp = importanceLevel(stats.avg_importance);

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3 animate-fade-in">
      {/* Total memories */}
      <StatTile
        icon={Brain}
        label="Memories"
        value={stats.total_memories}
        color="text-brand-600 dark:text-brand-400"
        bgColor="bg-brand-100 dark:bg-brand-900/30"
      />
      {/* Connections */}
      <StatTile
        icon={Link2}
        label="Connections"
        value={stats.total_connections}
        color="text-violet-600 dark:text-violet-400"
        bgColor="bg-violet-100 dark:bg-violet-900/30"
      />
      {/* Resurfaced */}
      <StatTile
        icon={Lightbulb}
        label="Resurfaced"
        value={stats.total_resurfaced}
        color="text-amber-600 dark:text-amber-400"
        bgColor="bg-amber-100 dark:bg-amber-900/30"
      />
      {/* Avg Importance */}
      <StatTile
        icon={TrendingUp}
        label="Avg Score"
        value={stats.avg_importance}
        color={imp.color}
        bgColor="bg-surface-100 dark:bg-gray-800"
      />
      {/* Random Inspiration */}
      <button
        onClick={handleInspire}
        disabled={inspiring || stats.total_memories === 0}
        className="flex flex-col items-center justify-center gap-1.5 rounded-2xl border border-dashed border-surface-300 dark:border-gray-700 bg-surface-50 dark:bg-gray-800 p-4 text-center transition-all hover:border-brand-400 hover:bg-brand-50 dark:hover:bg-brand-950/30 active:scale-95 disabled:opacity-50 col-span-2 sm:col-span-4 lg:col-span-1"
      >
        {inspiring ? (
          <Loader2 className="h-5 w-5 animate-spin text-brand-500" />
        ) : (
          <Shuffle className="h-5 w-5 text-brand-500" />
        )}
        <span className="text-xs font-medium text-brand-700 dark:text-brand-400">Random Inspiration</span>
      </button>
    </div>
  );
}

/* ── Stat Tile ──────────────────────────────────────────── */

function StatTile({
  icon: Icon,
  label,
  value,
  color,
  bgColor,
}: {
  icon: React.ElementType;
  label: string;
  value: number;
  color: string;
  bgColor: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-1.5 rounded-2xl border border-surface-300 dark:border-gray-700/50 p-4 text-center",
        bgColor
      )}
    >
      <Icon className={cn("h-5 w-5", color)} />
      <span className="text-2xl font-bold text-surface-900 dark:text-white">{value}</span>
      <span className="text-[11px] text-surface-500 dark:text-gray-400 font-medium uppercase tracking-wider">
        {label}
      </span>
    </div>
  );
}
