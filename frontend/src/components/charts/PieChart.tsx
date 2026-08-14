"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { ChartConfig } from "@/lib/types";
import { CHART_COLORS } from "@/lib/constants";

interface Props {
  data: Record<string, unknown>[];
  config: ChartConfig;
}

export function PieChartView({ data, config }: Props) {
  const nameKey = config.xKey || Object.keys(data[0] || {})[0];
  const valueKey = config.yKey || Object.keys(data[0] || {})[1];

  return (
    <ResponsiveContainer width="100%" height={400}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          outerRadius={150}
          innerRadius={60}
          dataKey={valueKey}
          nameKey={nameKey}
          label={({ name, percent }) =>
            `${name}: ${percent ? (percent * 100).toFixed(1) : 0}%`
          }
          animationDuration={800}
        >
          {data.map((_, index) => (
            <Cell
              key={`cell-${index}`}
              fill={CHART_COLORS[index % CHART_COLORS.length]}
            />
          ))}
        </Pie>
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
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
