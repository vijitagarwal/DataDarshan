"use client";

interface Props {
  sql: string;
}

export function SQLViewer({ sql }: Props) {
  if (!sql) {
    return (
      <p className="text-muted-foreground text-center py-8">
        No SQL generated
      </p>
    );
  }

  return (
    <div className="relative">
      <pre className="p-4 rounded-lg bg-muted/50 border overflow-x-auto text-sm font-mono text-foreground leading-relaxed">
        {sql}
      </pre>
      <button
        className="absolute top-2 right-2 px-2 py-1 text-xs rounded bg-primary/10 hover:bg-primary/20 text-primary transition-colors"
        onClick={() => navigator.clipboard.writeText(sql)}
      >
        Copy
      </button>
    </div>
  );
}
