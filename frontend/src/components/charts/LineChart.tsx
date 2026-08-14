"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { ChartConfig } from "@/lib/types";
import { CHART_COLORS } from "@/lib/constants";

interface Props {
  data: Record<string, unknown>[];
  config: ChartConfig;
}

export function LineChartView({ data, config }: Props) {
  const xKey = config.xKey || Object.keys(data[0] || {})[0];
  const yKey = config.yKey || Object.keys(data[0] || {})[1];
  const groupKey = config.groupKey;

  if (groupKey && groupKey !== yKey && groupKey !== xKey) {
    const groups = [...new Set(data.map((d) => String(d[groupKey])))];
    const pivoted = new Map<string, Record<string, unknown>>();

    for (const row of data) {
      const key = String(row[xKey]);
      if (!pivoted.has(key)) {
        pivoted.set(key, { [xKey]: row[xKey] });
      }
      pivoted.get(key)![String(row[groupKey])] = row[yKey];
    }

    const pivotedData = [...pivoted.values()];

    return (
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={pivotedData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
          <XAxis dataKey={xKey} angle={-45} textAnchor="end" height={80} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
            }}
          />
          <Legend />
          {groups.map((g, i) => (
            <Line
              key={g}
              type="monotone"
              dataKey={g}
              stroke={CHART_COLORS[i % CHART_COLORS.length]}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 6 }}
              animationDuration={800}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
        <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
        <XAxis
          dataKey={xKey}
          angle={-45}
          textAnchor="end"
          height={80}
          tick={{ fontSize: 12 }}
        />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "8px",
          }}
          formatter={(value) => [
            typeof value === "number" ? value.toLocaleString() : String(value),
            ""
          ]}
        />
        <Line
          type="monotone"
          dataKey={yKey}
          stroke={CHART_COLORS[0]}
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 6 }}
          animationDuration={800}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
