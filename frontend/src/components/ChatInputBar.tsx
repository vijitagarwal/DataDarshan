"use client";

import React, { useState, useEffect } from "react";
import { Send, Sparkles, Loader2 } from "lucide-react";

interface ChatInputBarProps {
  onSend: (query: string) => void;
  isLoading?: boolean;
  suggestedQuestions?: string[];
}

export const ChatInputBar: React.FC<ChatInputBarProps> = ({
  onSend,
  isLoading = false,
  suggestedQuestions = [],
}) => {
  const [inputQuery, setInputQuery] = useState("");
  const [placeholderIndex, setPlaceholderIndex] = useState(0);

  const defaultPlaceholders = [
    "Ask anything about your data... (e.g., Show revenue by product category)",
    "Try: Show monthly sales trends for 2023",
    "Try: What are the top 5 regions by total sales?",
    "Try: Count total orders by fulfillment channel",
  ];

  const placeholders = suggestedQuestions.length > 0
    ? suggestedQuestions.map((q) => `Try: ${q}`)
    : defaultPlaceholders;

  useEffect(() => {
    const timer = setInterval(() => {
      setPlaceholderIndex((prev) => (prev + 1) % placeholders.length);
    }, 4500);
    return () => clearInterval(timer);
  }, [placeholders.length]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || isLoading) return;
    onSend(inputQuery.trim());
    setInputQuery("");
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-3 sticky bottom-0 z-20">
      <form
        onSubmit={handleSubmit}
        className="glass-card p-2 flex items-center gap-2 border border-indigo-500/30 focus-within:border-indigo-500 shadow-2xl shadow-indigo-950/50 bg-[#141b2d]/95 backdrop-blur-md rounded-2xl transition-all"
      >
        <div className="pl-3 text-indigo-400">
          <Sparkles className="w-5 h-5" />
        </div>

        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder={placeholders[placeholderIndex]}
          disabled={isLoading}
          className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-400 focus:outline-none px-2 py-2"
        />

        <button
          type="submit"
          disabled={!inputQuery.trim() || isLoading}
          className={`p-2.5 rounded-xl transition-all flex items-center justify-center ${
            inputQuery.trim() && !isLoading
              ? "btn-primary text-white cursor-pointer"
              : "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
          }`}
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
      </form>
    </div>
  );
};
