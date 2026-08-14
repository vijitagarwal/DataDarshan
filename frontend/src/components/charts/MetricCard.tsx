"use client";

import { ChartConfig } from "@/lib/types";
import { DollarSign, Hash, Percent } from "lucide-react";

interface Props {
  data: Record<string, unknown>[];
  config: ChartConfig;
}

function formatValue(value: unknown, format: string): string {
  const num = Number(value);
  if (isNaN(num)) return String(value);

  switch (format) {
    case "currency":
      return `$${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    case "percent":
      return `${num.toFixed(1)}%`;
    case "number":
    default:
      return num.toLocaleString();
  }
}

function getIcon(format: string) {
  switch (format) {
    case "currency":
      return <DollarSign className="h-5 w-5" />;
    case "percent":
      return <Percent className="h-5 w-5" />;
    default:
      return <Hash className="h-5 w-5" />;
  }
}

export function MetricCard({ data, config }: Props) {
  const row = data[0] || {};
  const metrics = config.metrics || [];

  // If no metrics defined, create them from data keys
  const displayMetrics =
    metrics.length > 0
      ? metrics
      : Object.keys(row).map((key) => ({
          label: key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
          key,
          format: "number" as const,
        }));

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
      {displayMetrics.map((metric) => (
        <div
          key={metric.key}
          className="flex flex-col items-center justify-center p-6 rounded-xl bg-gradient-to-br from-primary/5 to-primary/10 border border-border"
        >
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            {getIcon(metric.format)}
            <span className="text-sm font-medium">{metric.label}</span>
          </div>
          <span className="text-3xl font-bold text-foreground">
            {formatValue(row[metric.key], metric.format)}
          </span>
        </div>
      ))}
    </div>
  );
}
