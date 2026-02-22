"use client";

import { X, ExternalLink, Star, Tag, Link2, Brain } from "lucide-react";
import { cn, categoryColor, importanceLevel, timeAgo } from "@/lib/utils";
import type { Memory } from "@/lib/types";

interface InspireModalProps {
  memory: Memory | null;
  onClose: () => void;
}

export default function InspireModal({ memory, onClose }: InspireModalProps) {
  if (!memory) return null;

  const imp = importanceLevel(memory.importance_score);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="relative mx-4 w-full max-w-lg rounded-2xl border border-surface-200 bg-white p-6 shadow-2xl animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1 text-surface-400 hover:bg-surface-100 hover:text-surface-600 transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-2 mb-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-100">
            <Brain className="h-5 w-5 text-brand-600" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-surface-900">Random Inspiration</h3>
            <p className="text-xs text-surface-500">A memory worth revisiting</p>
          </div>
        </div>

        {/* Thumbnail */}
        {memory.thumbnail_url && (
          <div className="mb-4 overflow-hidden rounded-xl border border-surface-100">
            <img
              src={memory.thumbnail_url}
              alt=""
              className="h-48 w-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = "none";
              }}
            />
          </div>
        )}

        {/* Content */}
        <h4 className="text-base font-semibold text-surface-900 mb-1.5">
          {memory.title || "Untitled Memory"}
        </h4>
        <p className="text-sm text-surface-600 mb-3 leading-relaxed">
          {memory.summary || memory.content || "Saved content"}
        </p>

        {/* Meta */}
        <div className="flex items-center gap-2 flex-wrap mb-3">
          <span
            className={cn(
              "rounded-full border px-2.5 py-0.5 text-xs font-medium",
              categoryColor(memory.category)
            )}
          >
            {memory.category}
          </span>
          <div className="flex items-center gap-1">
            <Star className={cn("h-3.5 w-3.5", imp.color)} />
            <span className={cn("text-xs font-semibold", imp.color)}>
              {memory.importance_score}
            </span>
          </div>
          <span className="text-xs text-surface-400">{timeAgo(memory.created_at)}</span>
        </div>

        {/* Tags */}
        {memory.tags && memory.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {memory.tags.map((t) => (
              <span
                key={t}
                className="inline-flex items-center gap-0.5 rounded-md bg-surface-100 px-2 py-0.5 text-[11px] text-surface-600"
              >
                <Tag className="h-3 w-3" />
                {t}
              </span>
            ))}
          </div>
        )}

        {/* Topic Graph */}
        {memory.topic_graph && memory.topic_graph.length > 0 && (
          <div className="mb-4 rounded-xl bg-surface-50 p-3">
            <p className="text-[11px] font-semibold text-surface-500 uppercase tracking-wide mb-1">
              Topic Graph
            </p>
            <p className="text-sm text-surface-700">
              {memory.topic_graph.join(" → ")}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <a
            href={memory.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-1.5 rounded-xl bg-brand-600 py-2.5 text-sm font-medium text-white hover:bg-brand-700 transition-colors"
          >
            <ExternalLink className="h-4 w-4" />
            Open Original
          </a>
          <button
            onClick={onClose}
            className="rounded-xl border border-surface-200 px-4 py-2.5 text-sm font-medium text-surface-600 hover:bg-surface-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
