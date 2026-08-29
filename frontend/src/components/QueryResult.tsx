"use client";

import React, { useState } from "react";
import { QueryResponse, SavedChart } from "@/lib/types";
import { KpiTiles } from "./KpiTiles";
import { ChartView } from "./ChartView";
import { InsightCard } from "./InsightCard";
import { FilterPills } from "./FilterPills";
import { Download, BookmarkCheck, Bookmark, Link2, Table, ChevronDown, ChevronUp } from "lucide-react";

interface QueryResultProps {
  entryIndex: number;
  response: QueryResponse;
  onSaveChart?: (savedItem: SavedChart) => void;
  isSaved?: boolean;
}

export const QueryResult: React.FC<QueryResultProps> = ({
  entryIndex,
  response,
  onSaveChart,
  isSaved = false,
}) => {
  const [showFullTable, setShowFullTable] = useState(false);
  const [chartOverride, setChartOverride] = useState<string>("auto");

  const query = response.query;
  const result = response.result;
  const parsed = response.parsed;
  const insight = response.insight;
  const fallback = response.fallback;
  const usedContext = response.used_context;

  if (response.error || result?.error) {
    return (
      <div className="w-full mb-8">
        {/* User Query Bubble */}
        <div className="flex justify-end mb-4">
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 max-w-[80%] text-sm font-medium shadow-lg shadow-indigo-500/20">
            {query}
          </div>
        </div>

        {/* Error Card */}
        <div className="glass-card p-4 border-red-500/30 bg-red-950/20 text-red-300 text-sm">
          ⚠️ {response.message || result?.message || "Error running query. Please try rephrasing."}
        </div>
      </div>
    );
  }

  const summary = result?.summary || {};
  const metric = result?.metric || "value";
  const dataRows = result?.data || [];

  // Download CSV handler
  const handleDownloadCSV = () => {
    if (!dataRows || dataRows.length === 0) return;
    const keys = Object.keys(dataRows[0]);
    const escapeCell = (value: unknown) => `"${String(value ?? "").replace(/"/g, '""')}"`;
    const csvContent = [
      keys.map(escapeCell).join(","),
      ...dataRows.map((row) => keys.map((key) => escapeCell(row[key])).join(",")),
    ].join("\n");
    const encodedUri = `data:text/csv;charset=utf-8,${encodeURIComponent(csvContent)}`;
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `query_${entryIndex}_${metric}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleSave = () => {
    if (onSaveChart) {
      onSaveChart({
        id: `saved-${Date.now()}`,
        query,
        insight,
        summary,
        metric,
        timestamp: Date.now(),
        response,
      });
    }
  };

  return (
    <div className="w-full mb-8 animate-fadeIn">
      {/* User Query Bubble */}
      <div className="flex justify-end mb-4">
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 max-w-[80%] text-sm font-medium shadow-lg shadow-indigo-500/20 flex items-center gap-2">
          <span>{query}</span>
          {usedContext && (
            <span className="inline-flex items-center gap-1 text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full font-semibold">
              <Link2 className="w-3 h-3" /> Follow-up
            </span>
          )}
        </div>
      </div>

      {/* Active Filters */}
      {parsed?.filters && <FilterPills filters={parsed.filters} />}

      {/* Row 1: KPI Tiles */}
      <KpiTiles summary={summary} metric={metric} />

      {/* Row 2: Chart (70%) + Insight (30%) */}
      <div className="grid grid-cols-1 lg:grid-cols-10 gap-4 mb-4">
        {/* Left 7 cols: Chart Card */}
        <div className="lg:col-span-7 glass-card p-4 flex flex-col justify-between">
          <ChartView
            result={result!}
            plotlySpec={response.plotly_spec}
            chartTypeOverride={chartOverride}
            onChartTypeChange={(t) => setChartOverride(t)}
          />

          {/* Action Bar: Download CSV & Save Chart */}
          <div className="flex items-center justify-between pt-3 border-t border-indigo-500/10 mt-2">
            <button
              onClick={handleDownloadCSV}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 hover:bg-emerald-500/20 transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download CSV</span>
            </button>

            <button
              onClick={handleSave}
              disabled={isSaved}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                isSaved
                  ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 cursor-default"
                  : "bg-indigo-600/10 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-600/20"
              }`}
            >
              {isSaved ? (
                <>
                  <BookmarkCheck className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Saved</span>
                </>
              ) : (
                <>
                  <Bookmark className="w-3.5 h-3.5" />
                  <span>Save Chart</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right 3 cols: Insight & Preview Table */}
        <div className="lg:col-span-3 flex flex-col gap-3">
          <InsightCard insight={insight} fallback={fallback} />

          {dataRows.length > 0 && (
            <div className="glass-card p-3 flex-1 flex flex-col">
              <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-indigo-400 mb-2">
                <Table className="w-3.5 h-3.5" />
                <span>Top Records Preview</span>
              </div>
              <div className="overflow-x-auto text-xs">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-indigo-500/20 text-slate-400">
                      {Object.keys(dataRows[0]).slice(0, 3).map((col) => (
                        <th key={col} className="pb-1 px-1 font-semibold truncate">
                          {col.replace(/_/g, " ")}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {dataRows.slice(0, 5).map((row, idx) => (
                      <tr key={idx} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                        {Object.keys(dataRows[0]).slice(0, 3).map((col) => (
                          <td key={col} className="py-1 px-1 text-slate-300 truncate max-w-[100px]">
                            {String(row[col])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Row 3: Expandable Full Dataset View */}
      {dataRows.length > 0 && (
        <div className="glass-card p-3">
          <button
            onClick={() => setShowFullTable(!showFullTable)}
            className="w-full flex items-center justify-between text-xs font-semibold text-slate-400 hover:text-slate-200"
          >
            <span>View Complete Query Result ({dataRows.length} rows)</span>
            {showFullTable ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showFullTable && (
            <div className="mt-3 overflow-x-auto max-h-[300px]">
              <table className="w-full text-xs text-left border-collapse">
                <thead className="sticky top-0 bg-slate-900 text-slate-300 border-b border-indigo-500/30">
                  <tr>
                    {Object.keys(dataRows[0]).map((col) => (
                      <th key={col} className="py-2 px-3 font-semibold">
                        {col.replace(/_/g, " ")}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {dataRows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-800/40 text-slate-300">
                      {Object.keys(dataRows[0]).map((col) => (
                        <td key={col} className="py-1.5 px-3">
                          {String(row[col])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
