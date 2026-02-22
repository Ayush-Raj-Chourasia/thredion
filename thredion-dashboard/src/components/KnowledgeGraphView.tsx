"use client";

import { useEffect, useRef, useState } from "react";
import { Network, Loader2 } from "lucide-react";
import { cn, categoryDotColor } from "@/lib/utils";
import type { KnowledgeGraph } from "@/lib/types";
import { getGraph } from "@/lib/api";

export default function KnowledgeGraphView() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [graph, setGraph] = useState<KnowledgeGraph | null>(null);
  const [loading, setLoading] = useState(true);
  const [hoveredNode, setHoveredNode] = useState<number | null>(null);

  // Node positions (force-directed simulation)
  const positionsRef = useRef<Map<number, { x: number; y: number; vx: number; vy: number }>>(
    new Map()
  );

  useEffect(() => {
    getGraph()
      .then(setGraph)
      .catch(() => setGraph(null))
      .finally(() => setLoading(false));
  }, []);

  // Initialize positions when graph loads
  useEffect(() => {
    if (!graph || graph.nodes.length === 0) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const W = canvas.width;
    const H = canvas.height;
    const positions = positionsRef.current;

    // Initialize random positions
    graph.nodes.forEach((node) => {
      if (!positions.has(node.id)) {
        positions.set(node.id, {
          x: W * 0.2 + Math.random() * W * 0.6,
          y: H * 0.2 + Math.random() * H * 0.6,
          vx: 0,
          vy: 0,
        });
      }
    });

    // Simple force-directed layout (runs once with iterations)
    const iterations = 100;
    for (let iter = 0; iter < iterations; iter++) {
      const alpha = 1 - iter / iterations;

      // Repulsion between all nodes
      for (let i = 0; i < graph.nodes.length; i++) {
        for (let j = i + 1; j < graph.nodes.length; j++) {
          const a = positions.get(graph.nodes[i].id)!;
          const b = positions.get(graph.nodes[j].id)!;
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (300 * alpha) / dist;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          a.vx -= fx;
          a.vy -= fy;
          b.vx += fx;
          b.vy += fy;
        }
      }

      // Attraction along edges
      graph.edges.forEach((edge) => {
        const a = positions.get(edge.source);
        const b = positions.get(edge.target);
        if (!a || !b) return;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = dist * 0.01 * alpha;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        a.vx += fx;
        a.vy += fy;
        b.vx -= fx;
        b.vy -= fy;
      });

      // Apply velocities
      positions.forEach((pos) => {
        pos.x += pos.vx;
        pos.y += pos.vy;
        pos.vx *= 0.9;
        pos.vy *= 0.9;
        // Clamp to canvas bounds
        pos.x = Math.max(40, Math.min(W - 40, pos.x));
        pos.y = Math.max(40, Math.min(H - 40, pos.y));
      });
    }

    // Draw
    drawGraph(canvas, graph, positions, hoveredNode);
  }, [graph, hoveredNode]);

  // Handle canvas resize
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const resize = () => {
      const parent = canvas.parentElement;
      if (!parent) return;
      canvas.width = parent.clientWidth;
      canvas.height = Math.max(400, parent.clientHeight);
      if (graph) {
        drawGraph(canvas, graph, positionsRef.current, hoveredNode);
      }
    };

    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, [graph, hoveredNode]);

  // Mouse hover
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!graph || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    let found: number | null = null;
    positionsRef.current.forEach((pos, id) => {
      const dx = pos.x - mx;
      const dy = pos.y - my;
      if (dx * dx + dy * dy < 20 * 20) {
        found = id;
      }
    });
    if (found !== hoveredNode) setHoveredNode(found);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-surface-400" />
      </div>
    );
  }

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-surface-300 bg-surface-50 p-10 text-center">
        <Network className="mx-auto mb-3 h-10 w-10 text-surface-400" />
        <p className="text-sm font-medium text-surface-600">Knowledge graph is empty</p>
        <p className="mt-1 text-xs text-surface-400">
          Save at least 2 related memories to see connections.
        </p>
      </div>
    );
  }

  // Legend
  const uniqueCategories = Array.from(new Set(graph.nodes.map((n) => n.category)));

  return (
    <div className="space-y-3 animate-fade-in">
      <div className="flex items-center gap-2">
        <Network className="h-5 w-5 text-violet-500" />
        <h2 className="text-base font-semibold text-surface-900">Knowledge Graph</h2>
        <span className="text-xs text-surface-500">
          {graph.nodes.length} nodes · {graph.edges.length} edges
        </span>
      </div>

      <div className="relative rounded-2xl border border-surface-200 bg-white overflow-hidden">
        <canvas
          ref={canvasRef}
          width={800}
          height={500}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoveredNode(null)}
          className="w-full cursor-crosshair"
          style={{ minHeight: "400px" }}
        />

        {/* Hovered node tooltip */}
        {hoveredNode !== null && (() => {
          const node = graph.nodes.find((n) => n.id === hoveredNode);
          const pos = positionsRef.current.get(hoveredNode);
          if (!node || !pos) return null;
          return (
            <div
              className="absolute z-10 rounded-lg bg-surface-900 px-3 py-2 text-xs text-white shadow-lg pointer-events-none"
              style={{ left: pos.x + 20, top: pos.y - 10 }}
            >
              <p className="font-medium">{node.title}</p>
              <p className="text-surface-300">{node.category} · Score: {node.importance_score}</p>
            </div>
          );
        })()}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 px-1">
        {uniqueCategories.map((cat) => (
          <div key={cat} className="flex items-center gap-1.5">
            <span
              className="h-3 w-3 rounded-full"
              style={{ backgroundColor: categoryDotColor(cat) }}
            />
            <span className="text-[11px] text-surface-600">{cat}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Canvas Drawing ────────────────────────────────────── */

function drawGraph(
  canvas: HTMLCanvasElement,
  graph: KnowledgeGraph,
  positions: Map<number, { x: number; y: number; vx: number; vy: number }>,
  hoveredNode: number | null
) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Draw edges
  graph.edges.forEach((edge) => {
    const a = positions.get(edge.source);
    const b = positions.get(edge.target);
    if (!a || !b) return;

    const isHighlighted =
      hoveredNode !== null && (edge.source === hoveredNode || edge.target === hoveredNode);

    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.strokeStyle = isHighlighted ? "rgba(76, 110, 245, 0.5)" : "rgba(206, 212, 218, 0.5)";
    ctx.lineWidth = isHighlighted ? 2.5 : 1;
    ctx.stroke();

    // Weight label on highlighted edges
    if (isHighlighted) {
      const mx = (a.x + b.x) / 2;
      const my = (a.y + b.y) / 2;
      ctx.fillStyle = "#4c6ef5";
      ctx.font = "10px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(`${Math.round(edge.weight * 100)}%`, mx, my - 5);
    }
  });

  // Draw nodes
  graph.nodes.forEach((node) => {
    const pos = positions.get(node.id);
    if (!pos) return;

    const isHovered = hoveredNode === node.id;
    const color = categoryDotColor(node.category);
    const radius = isHovered ? 14 : 8 + (node.importance_score / 100) * 6;

    // Outer glow for hovered
    if (isHovered) {
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius + 6, 0, Math.PI * 2);
      ctx.fillStyle = color + "20";
      ctx.fill();
    }

    // Node circle
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = isHovered ? "#fff" : color;
    ctx.lineWidth = isHovered ? 3 : 1;
    ctx.stroke();

    // Label
    ctx.fillStyle = "#343a40";
    ctx.font = `${isHovered ? "bold " : ""}11px Inter, sans-serif`;
    ctx.textAlign = "center";
    const label =
      node.title.length > 20 ? node.title.slice(0, 20) + "…" : node.title;
    ctx.fillText(label, pos.x, pos.y + radius + 14);
  });
}
