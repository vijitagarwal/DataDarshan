"use client";

import { Badge } from "@/components/ui/badge";

interface Props {
  suggestions: string[];
  onSelect: (query: string) => void;
}

export function SuggestedChips({ suggestions, onSelect }: Props) {
  if (!suggestions.length) return null;

  return (
    <div className="flex flex-wrap gap-2 px-4 pb-3">
      {suggestions.map((s, i) => (
        <Badge
          key={i}
          variant="outline"
          className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors py-1.5 px-3 text-xs"
          onClick={() => onSelect(s)}
        >
          {s}
        </Badge>
      ))}
    </div>
  );
}
