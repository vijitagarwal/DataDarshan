"use client";

import { QueryResponse } from "@/lib/types";
import { BarChartView } from "./BarChart";
import { LineChartView } from "./LineChart";
import { PieChartView } from "./PieChart";
import { ScatterChartView } from "./ScatterChart";
import { MetricCard } from "./MetricCard";
import { DataTable } from "./DataTable";
import { AlertCircle } from "lucide-react";

interface ChartRendererProps {
  response: QueryResponse;
}

export function ChartRenderer({ response }: ChartRendererProps) {
  const { data, chart_type, chart_config } = response;

  if (chart_type === "error") {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <AlertCircle className="h-12 w-12 mb-4 text-destructive" />
        <p className="text-center max-w-md">{response.explanation}</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <p>No data to display</p>
      </div>
    );
  }

  switch (chart_type) {
    case "bar":
      return <BarChartView data={data} config={chart_config} />;
    case "line":
      return <LineChartView data={data} config={chart_config} />;
    case "pie":
      return <PieChartView data={data} config={chart_config} />;
    case "scatter":
      return <ScatterChartView data={data} config={chart_config} />;
    case "metric":
      return <MetricCard data={data} config={chart_config} />;
    case "table":
      return <DataTable data={data} />;
    default:
      return <BarChartView data={data} config={chart_config} />;
  }
}
