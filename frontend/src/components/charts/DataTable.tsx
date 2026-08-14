"use client";

import { ScrollArea } from "@/components/ui/scroll-area";

interface Props {
  data: Record<string, unknown>[];
}

export function DataTable({ data }: Props) {
  if (!data.length) return null;

  const columns = Object.keys(data[0]);

  return (
    <ScrollArea className="h-[400px] w-full rounded-md border">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-muted z-10">
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                className="text-left p-3 font-semibold text-foreground whitespace-nowrap border-b"
              >
                {col.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr
              key={i}
              className="border-b hover:bg-muted/50 transition-colors"
            >
              {columns.map((col) => (
                <td key={col} className="p-3 whitespace-nowrap text-muted-foreground">
                  {typeof row[col] === "number"
                    ? (row[col] as number).toLocaleString()
                    : String(row[col] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </ScrollArea>
  );
}
