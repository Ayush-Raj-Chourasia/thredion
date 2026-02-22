"use client";

import { Lightbulb, ArrowRight, ExternalLink } from "lucide-react";
import { cn, categoryColor, timeAgo, truncate } from "@/lib/utils";
import type { ResurfacedMemory } from "@/lib/types";

interface ResurfacedPanelProps {
  items: ResurfacedMemory[];
}

export default function ResurfacedPanel({ items }: ResurfacedPanelProps) {
  if (!items || items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-amber-300/50 bg-amber-50/30 p-6 text-center">
        <Lightbulb className="mx-auto mb-2 h-8 w-8 text-amber-400" />
        <p className="text-sm font-medium text-amber-800">No resurfaced insights yet</p>
        <p className="mt-1 text-xs text-amber-600">
          Save more memories — Thredion will surface forgotten insights when related content appears.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-1">
        <Lightbulb className="h-5 w-5 text-amber-500" />
        <h2 className="text-base font-semibold text-surface-900">
          Resurfaced Insights
        </h2>
        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-medium text-amber-700">
          {items.length}
        </span>
      </div>

      {items.map((item) => (
        <div
          key={item.id}
          className="relative rounded-xl border border-amber-200/60 bg-amber-50/40 p-4 transition-colors hover:bg-amber-50 animate-slide-up"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-surface-900 leading-snug">
                {truncate(item.memory_title, 80)}
              </p>
              <p className="mt-1 text-xs text-surface-600 leading-relaxed">
                {truncate(item.memory_summary, 120)}
              </p>

              {/* Triggered by */}
              <div className="mt-2 flex items-center gap-1.5 text-[11px] text-surface-500">
                <span>Triggered by</span>
                <ArrowRight className="h-3 w-3" />
                <span className="font-medium text-brand-600">
                  {truncate(item.triggered_by_title, 40)}
                </span>
              </div>

              {/* Reason */}
              <p className="mt-1.5 text-[11px] text-amber-700 italic">
                {item.reason}
              </p>

              <div className="mt-2 flex items-center gap-2">
                <span
                  className={cn(
                    "inline-flex rounded-full border px-2 py-0.5 text-[10px] font-medium",
                    categoryColor(item.memory_category)
                  )}
                >
                  {item.memory_category}
                </span>
                <span className="text-[10px] text-surface-400">
                  {Math.round(item.similarity_score * 100)}% similar
                </span>
                <span className="text-[10px] text-surface-400">
                  {timeAgo(item.created_at)}
                </span>
              </div>
            </div>

            <a
              href={item.memory_url}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 rounded-lg p-1.5 text-surface-400 hover:bg-amber-100 hover:text-amber-700 transition-colors"
            >
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}
