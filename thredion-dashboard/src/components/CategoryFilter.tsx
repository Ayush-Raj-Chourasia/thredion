"use client";

import { cn, categoryColor } from "@/lib/utils";

interface CategoryFilterProps {
  categories: { category: string; count: number }[];
  selected: string;
  onSelect: (cat: string) => void;
}

export default function CategoryFilter({
  categories,
  selected,
  onSelect,
}: CategoryFilterProps) {
  if (!categories || categories.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 animate-fade-in">
      <button
        onClick={() => onSelect("")}
        className={cn(
          "rounded-full border px-3 py-1 text-xs font-medium transition-all",
          selected === ""
            ? "border-brand-400 bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-400 dark:border-brand-600"
            : "border-surface-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-surface-600 dark:text-gray-400 hover:border-surface-400 dark:hover:border-gray-600"
        )}
      >
        All
      </button>
      {categories.map(({ category, count }) => (
        <button
          key={category}
          onClick={() => onSelect(category === selected ? "" : category)}
          className={cn(
            "rounded-full border px-3 py-1 text-xs font-medium transition-all",
            selected === category
              ? categoryColor(category)
              : "border-surface-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-surface-600 dark:text-gray-400 hover:border-surface-400 dark:hover:border-gray-600"
          )}
        >
          {category}{" "}
          <span className="ml-0.5 text-[10px] opacity-60">{count}</span>
        </button>
      ))}
    </div>
  );
}
