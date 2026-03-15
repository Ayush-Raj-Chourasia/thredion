
"use client";

import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Lightbulb, 
  User, 
  Calendar, 
  Tag, 
  TrendingUp, 
  ArrowRight,
  ChevronRight,
  Activity,
  Archive
} from 'lucide-react';
import { clsx } from 'clsx';

// --- Types ---

interface CognitiveEntry {
  id: string;
  cognitive_mode: 'learn' | 'think' | 'reflect';
  title: string;
  summary: string;
  bucket: string;
  tags: string[];
  actionability_score: number;
  emotional_tone?: string;
  created_at: string;
}

interface WeeklyStats {
  entries_by_mode: Record<string, number>;
  entries_by_bucket: { name: string; count: number }[];
  total_count: number;
  most_active_bucket: string | null;
}

// --- Components ---

const ModeTag = ({ mode }: { mode: string }) => {
  const styles = {
    learn: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    think: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    reflect: "bg-pink-500/10 text-pink-400 border-pink-500/20"
  };
  const icon = {
    learn: <BookOpen className="w-3 h-3 mr-1" />,
    think: <Lightbulb className="w-3 h-3 mr-1" />,
    reflect: <User className="w-3 h-3 mr-1" />
  };
  
  const m = mode.toLowerCase() as keyof typeof styles;
  
  return (
    <span className={clsx("flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium border uppercase tracking-wider", styles[m] || "bg-gray-500/10 text-gray-400")}>
      {icon[m]}
      {mode}
    </span>
  );
};

const CognitiveCard = ({ entry }: { entry: CognitiveEntry }) => (
  <div className="group relative bg-[#1A1A1A] border border-white/5 rounded-2xl p-6 hover:border-white/10 transition-all duration-300">
    <div className="flex justify-between items-start mb-4">
      <ModeTag mode={entry.cognitive_mode} />
      <span className="text-[10px] text-white/30 font-medium uppercase tracking-widest flex items-center">
        <Calendar className="w-3 h-3 mr-1" />
        {new Date(entry.created_at).toLocaleDateString()}
      </span>
    </div>
    
    <h3 className="text-lg font-semibold text-white/90 mb-2 truncate group-hover:text-blue-400 transition-colors">
      {entry.title}
    </h3>
    
    <p className="text-sm text-white/50 line-clamp-2 mb-4 leading-relaxed">
      {entry.summary}
    </p>
    
    <div className="flex items-center justify-between pt-4 border-t border-white/5">
      <div className="flex items-center space-x-2">
        <span className="text-[10px] text-white/30 uppercase font-bold">Actionability</span>
        <div className="w-24 h-1 bg-white/5 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-blue-500 to-purple-500" 
            style={{ width: `${entry.actionability_score * 100}%` }}
          />
        </div>
      </div>
      <div className="text-[10px] text-white/40 flex items-center bg-white/5 px-2 py-1 rounded-md">
        <Archive className="w-3 h-3 mr-1" />
        {entry.bucket}
      </div>
    </div>
  </div>
);

// --- Main Page ---

export default function CognitiveDashboard() {
  const [activeTab, setActiveTab] = useState<'all' | 'learn' | 'think' | 'reflect'>('all');
  const [entries, setEntries] = useState<CognitiveEntry[]>([]);
  const [stats, setStats] = useState<WeeklyStats | null>(null);
  const [loading, setLoading] = useState(true);

  // Default test phone - in real app, get from auth context
  const phoneNumber = "918707701003"; 
  const apiBase = "http://localhost:8000/api/cognitive";

  useEffect(() => {
    async function fetchData() {
      try {
        const [dashRes, entriesRes] = await Promise.all([
          fetch(`${apiBase}/dashboard?phone_number=${phoneNumber}`),
          fetch(`${apiBase}/entries?phone_number=${phoneNumber}&limit=20`)
        ]);
        
        const dashData = await dashRes.json();
        const entriesData = await entriesRes.json();
        
        setStats(dashData);
        setEntries(entriesData);
      } catch (err) {
        console.error("Failed to fetch dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const filteredEntries = activeTab === 'all' 
    ? entries 
    : entries.filter(e => e.cognitive_mode === activeTab);

  if (loading) return (
    <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center text-white/20">
      <Activity className="animate-pulse w-8 h-8" />
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white selection:bg-blue-500/30">
      {/* Glossy Header Background */}
      <div className="absolute top-0 w-full h-64 bg-gradient-to-b from-blue-500/5 to-transparent border-b border-white/5" />
      
      <main className="relative max-w-7xl mx-auto px-6 pt-20 pb-32">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <span className="h-px w-8 bg-blue-500/50" />
              <span className="text-xs font-bold tracking-[0.3em] uppercase text-blue-400">Memory Layer</span>
            </div>
            <h1 className="text-6xl font-black tracking-tight leading-tight">
              Cognitive <br />
              <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 text-transparent bg-clip-text">
                Dashboard.
              </span>
            </h1>
          </div>
          
          <div className="grid grid-cols-3 gap-6 bg-[#1A1A1A] border border-white/5 p-6 rounded-3xl shadow-2xl">
            <div className="px-4 border-r border-white/5">
              <div className="text-[10px] text-white/30 uppercase font-black mb-1">Items Learned</div>
              <div className="text-2xl font-black text-blue-400">{stats?.entries_by_mode.learn || 0}</div>
            </div>
            <div className="px-4 border-r border-white/5">
              <div className="text-[10px] text-white/30 uppercase font-black mb-1">Ideas Born</div>
              <div className="text-2xl font-black text-purple-400">{stats?.entries_by_mode.think || 0}</div>
            </div>
            <div className="px-4">
              <div className="text-[10px] text-white/30 uppercase font-black mb-1">Self Reflex</div>
              <div className="text-2xl font-black text-pink-400">{stats?.entries_by_mode.reflect || 0}</div>
            </div>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="flex flex-wrap items-center gap-3 mb-10 pb-8 border-b border-white/5">
          {[
            { id: 'all', label: 'All Layers', icon: <TrendingUp className="w-4 h-4" /> },
            { id: 'learn', label: 'Learn', icon: <BookOpen className="w-4 h-4" /> },
            { id: 'think', label: 'Think', icon: <Lightbulb className="w-4 h-4" /> },
            { id: 'reflect', label: 'Reflect', icon: <User className="w-4 h-4" /> },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={clsx(
                "flex items-center space-x-2 px-6 py-3 rounded-xl text-sm font-bold transition-all duration-300 border",
                activeTab === tab.id 
                  ? "bg-white text-black border-white" 
                  : "bg-transparent text-white/40 border-white/5 hover:border-white/20 hover:text-white"
              )}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredEntries.map((entry) => (
            <CognitiveCard key={entry.id} entry={entry} />
          ))}
          
          {filteredEntries.length === 0 && (
            <div className="col-span-full py-32 flex flex-col items-center border border-dashed border-white/5 rounded-3xl">
              <Archive className="w-12 h-12 text-white/10 mb-4" />
              <p className="text-white/20 font-medium">No cognitive records captured yet.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
