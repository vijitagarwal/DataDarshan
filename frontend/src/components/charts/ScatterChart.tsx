"use client";

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { ChartConfig } from "@/lib/types";
import { CHART_COLORS } from "@/lib/constants";

interface Props {
  data: Record<string, unknown>[];
  config: ChartConfig;
}

export function ScatterChartView({ data, config }: Props) {
  const xKey = config.xKey || Object.keys(data[0] || {})[0];
  const yKey = config.yKey || Object.keys(data[0] || {})[1];

  return (
    <ResponsiveContainer width="100%" height={400}>
      <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
        <XAxis
          dataKey={xKey}
          name={config.xLabel || xKey}
          tick={{ fontSize: 12 }}
          label={config.xLabel ? { value: config.xLabel, position: "bottom" } : undefined}
        />
        <YAxis
          dataKey={yKey}
          name={config.yLabel || yKey}
          tick={{ fontSize: 12 }}
          label={config.yLabel ? { value: config.yLabel, angle: -90, position: "insideLeft" } : undefined}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "8px",
          }}
          cursor={{ strokeDasharray: "3 3" }}
        />
        <Scatter
          data={data}
          fill={CHART_COLORS[0]}
          animationDuration={800}
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
