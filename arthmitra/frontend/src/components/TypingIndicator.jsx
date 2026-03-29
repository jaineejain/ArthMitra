import React from "react";

export default function TypingIndicator() {
  return (
    <div className="w-full flex justify-start">
      <div className="inline-flex items-center gap-2 rounded-2xl rounded-tl-sm bg-white px-4 py-3 shadow-sm dark:bg-slate-800">
        <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: "0s" }} />
        <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: "0.15s" }} />
        <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: "0.3s" }} />
        <span className="text-xs font-medium text-gray-500 dark:text-slate-400">Thinking…</span>
      </div>
    </div>
  );
}

