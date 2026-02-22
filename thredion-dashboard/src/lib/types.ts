/* ── Thredion Dashboard — API Types ─────────────────────── */

export interface Memory {
  id: number;
  url: string;
  platform: string;
  title: string;
  content: string;
  summary: string;
  category: string;
  tags: string[];
  topic_graph: string[];
  importance_score: number;
  importance_reasons: string[];
  thumbnail_url: string;
  user_phone: string;
  created_at: string;
  connections?: ConnectionBrief[];
}

export interface ConnectionBrief {
  connected_memory_id: number;
  connected_memory_title: string;
  connected_memory_summary: string;
  connected_memory_category: string;
  similarity_score: number;
}

export interface ResurfacedMemory {
  id: number;
  memory_id: number;
  memory_title: string;
  memory_summary: string;
  memory_category: string;
  memory_url: string;
  triggered_by_id: number;
  triggered_by_title: string;
  reason: string;
  similarity_score: number;
  created_at: string;
}

export interface GraphNode {
  id: number;
  title: string;
  category: string;
  importance_score: number;
  url: string;
}

export interface GraphEdge {
  source: number;
  target: number;
  weight: number;
}

export interface KnowledgeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Stats {
  total_memories: number;
  total_connections: number;
  total_resurfaced: number;
  categories: Record<string, number>;
  avg_importance: number;
  top_category: string;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface ProcessResult {
  memory_id: number;
  url: string;
  platform: string;
  title: string;
  summary: string;
  category: string;
  tags: string[];
  topic_graph: string[];
  importance_score: number;
  importance_reasons: string[];
  connections: any[];
  resurfaced: any[];
  thumbnail_url: string;
  duplicate?: boolean;
  message?: string;
}
