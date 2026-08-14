"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { QueryResponse } from "@/lib/types";
import { ChartRenderer } from "@/components/charts/ChartRenderer";
import { DataTable } from "@/components/charts/DataTable";
import { SQLViewer } from "./SQLViewer";
import { BarChart3, Table, Code, Lightbulb } from "lucide-react";

interface Props {
  response: QueryResponse | null;
}

export function DashboardPanel({ response }: Props) {
  if (!response) {
    return null;
  }

  const chartTitle = response.chart_config?.title || "Query Results";

  return (
    <Card className="h-full border-0 shadow-none">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-semibold">{chartTitle}</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="chart" className="w-full">
          <TabsList className="mb-4">
            <TabsTrigger value="chart" className="gap-1.5">
              <BarChart3 className="h-3.5 w-3.5" />
              Chart
            </TabsTrigger>
            <TabsTrigger value="table" className="gap-1.5">
              <Table className="h-3.5 w-3.5" />
              Data
            </TabsTrigger>
            <TabsTrigger value="sql" className="gap-1.5">
              <Code className="h-3.5 w-3.5" />
              SQL
            </TabsTrigger>
          </TabsList>

          <TabsContent value="chart">
            <ChartRenderer response={response} />
          </TabsContent>

          <TabsContent value="table">
            {response.data && response.data.length > 0 ? (
              <DataTable data={response.data} />
            ) : (
              <p className="text-muted-foreground text-center py-8">
                No data to display
              </p>
            )}
          </TabsContent>

          <TabsContent value="sql">
            <SQLViewer sql={response.sql} />
          </TabsContent>
        </Tabs>

        {response.explanation && response.chart_type !== "error" && (
          <div className="mt-4 p-4 rounded-lg bg-muted/50 border border-border">
            <div className="flex items-start gap-2">
              <Lightbulb className="h-4 w-4 mt-0.5 text-amber-500 flex-shrink-0" />
              <p className="text-sm text-muted-foreground leading-relaxed">
                {response.explanation}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
