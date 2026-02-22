"use client";

import {
  ExternalLink,
  Star,
  Tag,
  Link2,
  Trash2,
  ChevronDown,
  ChevronUp,
  Instagram,
  Twitter,
  Youtube,
  FileText,
  Link,
  Play,
} from "lucide-react";
import { useState } from "react";
import { cn, categoryColor, importanceLevel, timeAgo, truncate, platformName } from "@/lib/utils";
import type { Memory } from "@/lib/types";

interface MemoryCardProps {
  memory: Memory;
  onDelete?: (id: number) => void;
}

const PlatformIcons: Record<string, React.ElementType> = {
  instagram: Instagram,
  twitter: Twitter,
  youtube: Youtube,
  article: FileText,
};

/** Extract a YouTube embed URL from the original link. */
function getYouTubeEmbedUrl(url: string): string | null {
  try {
    const u = new URL(url);
    let videoId: string | null = null;
    if (u.hostname.includes("youtu.be")) {
      videoId = u.pathname.slice(1);
    } else if (u.hostname.includes("youtube.com")) {
      videoId = u.searchParams.get("v");
      if (!videoId) {
        const m = u.pathname.match(/\/(?:embed|shorts)\/([^/?]+)/);
        if (m) videoId = m[1];
      }
    }
    return videoId ? `https://www.youtube.com/embed/${videoId}` : null;
  } catch {
    return null;
  }
}

/** Extract an Instagram embed URL from the original link. */
function getInstagramEmbedUrl(url: string): string | null {
  try {
    const m = url.match(/instagram\.com\/(?:p|reel|reels)\/([A-Za-z0-9_-]+)/);
    return m ? `https://www.instagram.com/p/${m[1]}/embed` : null;
  } catch {
    return null;
  }
}

export default function MemoryCard({ memory, onDelete }: MemoryCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [showEmbed, setShowEmbed] = useState(false);
  const imp = importanceLevel(memory.importance_score);
  const PlatformIcon = PlatformIcons[memory.platform] || Link;

  // Derive embed URL for supported platforms
  const embedUrl =
    memory.platform === "youtube" ? getYouTubeEmbedUrl(memory.url) :
    memory.platform === "instagram" ? getInstagramEmbedUrl(memory.url) :
    null;

  return (
    <div className="group relative rounded-2xl border border-surface-200 bg-white p-5 shadow-sm transition-all hover:shadow-md hover:border-surface-300 animate-fade-in">
      {/* Top Row: platform badge + time + actions */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-100 text-surface-600">
            <PlatformIcon className="h-4 w-4" />
          </div>
          <span className="text-xs font-medium text-surface-500 uppercase tracking-wide">
            {platformName(memory.platform)}
          </span>
          <span className="text-xs text-surface-400">•</span>
          <span className="text-xs text-surface-400">{timeAgo(memory.created_at)}</span>
        </div>
        <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <a
            href={memory.url}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg p-1.5 text-surface-400 hover:bg-surface-100 hover:text-surface-600 transition-colors"
            title="Open original link"
          >
            <ExternalLink className="h-4 w-4" />
          </a>
          {onDelete && (
            <button
              onClick={() => onDelete(memory.id)}
              className="rounded-lg p-1.5 text-surface-400 hover:bg-red-50 hover:text-red-500 transition-colors"
              title="Delete memory"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Embed / Thumbnail */}
      {showEmbed && embedUrl ? (
        <div className="mb-3 overflow-hidden rounded-xl border border-surface-100">
          <iframe
            src={embedUrl}
            title={memory.title || "Embedded content"}
            className="w-full aspect-video"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      ) : memory.thumbnail_url ? (
        <div className="relative mb-3 overflow-hidden rounded-xl border border-surface-100 cursor-pointer" onClick={() => embedUrl && setShowEmbed(true)}>
          <img
            src={memory.thumbnail_url}
            alt={memory.title || "thumbnail"}
            className="h-40 w-full object-cover transition-transform group-hover:scale-105"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
          {embedUrl && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/90 shadow-lg">
                <Play className="h-5 w-5 text-brand-600 ml-0.5" />
              </div>
            </div>
          )}
        </div>
      ) : null}

      {/* Title */}
      <h3 className="text-base font-semibold text-surface-900 leading-snug mb-1.5">
        {truncate(memory.title || "Untitled Memory", 80)}
      </h3>

      {/* Summary */}
      <p className="text-sm text-surface-600 leading-relaxed mb-3">
        {truncate(memory.summary || memory.content || "No summary available.", 150)}
      </p>

      {/* Category & Importance row */}
      <div className="flex items-center gap-2 flex-wrap mb-3">
        <span
          className={cn(
            "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
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
          <span className="text-[10px] text-surface-400 ml-0.5">{imp.label}</span>
        </div>
      </div>

      {/* Tags */}
      {memory.tags && memory.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {memory.tags.slice(0, 5).map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-0.5 rounded-md bg-surface-100 px-2 py-0.5 text-[11px] text-surface-600"
            >
              <Tag className="h-3 w-3" />
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Expandable: Topic Graph + Importance Reasons + Connections */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs text-surface-400 hover:text-surface-600 transition-colors"
      >
        {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        {expanded ? "Less details" : "More details"}
      </button>

      {expanded && (
        <div className="mt-3 space-y-3 border-t border-surface-100 pt-3 animate-fade-in">
          {/* Topic Graph */}
          {memory.topic_graph && memory.topic_graph.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold text-surface-500 uppercase tracking-wide mb-1">
                Topic Graph
              </p>
              <p className="text-sm text-surface-700">
                {memory.topic_graph.join(" → ")}
              </p>
            </div>
          )}

          {/* Importance Breakdown */}
          {memory.importance_reasons && memory.importance_reasons.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold text-surface-500 uppercase tracking-wide mb-1">
                Importance Breakdown
              </p>
              <ul className="space-y-0.5">
                {memory.importance_reasons.map((r, i) => (
                  <li key={i} className="text-xs text-surface-600 flex items-center gap-1.5">
                    <span className="h-1 w-1 rounded-full bg-surface-400 shrink-0" />
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Connections */}
          {memory.connections && memory.connections.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold text-surface-500 uppercase tracking-wide mb-1">
                <Link2 className="inline h-3 w-3 mr-0.5" />
                Connected Memories
              </p>
              <ul className="space-y-1">
                {memory.connections.map((c) => (
                  <li key={c.connected_memory_id} className="text-xs text-surface-600">
                    <span className="font-medium text-surface-700">
                      {c.connected_memory_title}
                    </span>{" "}
                    <span className="text-surface-400">
                      ({Math.round(c.similarity_score * 100)}% similar · {c.connected_memory_category})
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Original URL */}
          <div>
            <p className="text-[11px] font-semibold text-surface-500 uppercase tracking-wide mb-1">
              Source
            </p>
            <a
              href={memory.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-brand-600 hover:underline break-all"
            >
              {memory.url}
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
