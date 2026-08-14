"use client";

import React from "react";
import { QuerySummary } from "@/lib/types";

interface KpiTilesProps {
  summary: QuerySummary;
  metric: string;
}

const REVENUE_METRICS = new Set(["total_revenue", "discounted_price", "price", "revenue", "sales"]);

function formatNumber(val: number | undefined, metric: str = ""): string {
  if (val === undefined || val === null || isNaN(val)) return "—";
  
  const metricLower = (metric || "").toLowerCase();
  const isCurrency = REVENUE_METRICS.has(metricLower) || metricLower.includes("revenue") || metricLower.includes("price");
  const prefix = isCurrency ? "$" : "";
  const sign = val < 0 ? "-" : "";
  const absVal = Math.abs(val);

  if (absVal >= 1_000_000) {
    return `${sign}${prefix}${(absVal / 1_000_000).toFixed(2)}M`;
  }
  if (absVal >= 1_000) {
    return `${sign}${prefix}${(absVal / 1_000).toFixed(1)}K`;
  }
  return `${sign}${prefix}${absVal.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
}

export const KpiTiles: React.FC<KpiTilesProps> = ({ summary, metric }) => {
  const totalStr = formatNumber(summary?.total, metric);
  const avgStr = formatNumber(summary?.average, metric);
  const topLabel = summary?.max_label || "—";
  const topValueStr = formatNumber(summary?.max_value, metric);

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
      {/* Tile 1: Total */}
      <div className="glass-card p-3.5 flex flex-col justify-between border border-indigo-500/20 hover:border-indigo-500/40 transition-colors">
        <span className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
          Total
        </span>
        <div className="text-xl md:text-2xl font-extrabold text-slate-50 mt-1 tracking-tight">
          {totalStr}
        </div>
        <span className="text-[11px] text-indigo-400 font-medium mt-1">
          Sum of {metric.replace(/_/g, " ")}
        </span>
      </div>

      {/* Tile 2: Average */}
      <div className="glass-card p-3.5 flex flex-col justify-between border border-indigo-500/20 hover:border-indigo-500/40 transition-colors">
        <span className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
          Avg per Group
        </span>
        <div className="text-xl md:text-2xl font-extrabold text-slate-50 mt-1 tracking-tight">
          {avgStr}
        </div>
        <span className="text-[11px] text-indigo-400 font-medium mt-1">
          Mean value
        </span>
      </div>

      {/* Tile 3: Top Performer */}
      <div className="glass-card p-3.5 flex flex-col justify-between border border-indigo-500/20 hover:border-indigo-500/40 transition-colors">
        <span className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
          Top Performer
        </span>
        <div className="text-lg md:text-xl font-bold text-slate-50 mt-1 truncate" title={topLabel}>
          {topLabel}
        </div>
        <span className="text-[11px] text-emerald-400 font-medium mt-1">
          Highest contribution
        </span>
      </div>

      {/* Tile 4: Top Value */}
      <div className="glass-card p-3.5 flex flex-col justify-between border border-indigo-500/20 hover:border-indigo-500/40 transition-colors">
        <span className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
          Top Value
        </span>
        <div className="text-xl md:text-2xl font-extrabold text-slate-50 mt-1 tracking-tight">
          {topValueStr}
        </div>
        <span className="text-[11px] text-emerald-400 font-medium mt-1">
          Peak metric value
        </span>
      </div>
    </div>
  );
};
