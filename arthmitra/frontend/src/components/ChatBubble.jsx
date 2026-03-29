import React from "react";

function renderInlineMarkdown(text) {
  // Supports **bold**
  const parts = [];
  let remaining = text;
  let key = 0;
  while (remaining.length) {
    const start = remaining.indexOf("**");
    if (start === -1) {
      parts.push(<React.Fragment key={key++}>{remaining}</React.Fragment>);
      break;
    }
    const before = remaining.slice(0, start);
    if (before) parts.push(<React.Fragment key={key++}>{before}</React.Fragment>);

    const end = remaining.indexOf("**", start + 2);
    if (end === -1) {
      // Unclosed token, render rest.
      parts.push(<React.Fragment key={key++}>{remaining}</React.Fragment>);
      break;
    }
    const boldText = remaining.slice(start + 2, end);
    parts.push(
      <strong key={key++} className="font-semibold">
        {boldText}
      </strong>
    );
    remaining = remaining.slice(end + 2);
  }
  return parts;
}

function formatTs(iso) {
  if (!iso) return null;
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-IN", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return null;
  }
}

export default function ChatBubble({ role, content, timestamp }) {
  const lines = String(content || "").split("\n");
  const blocks = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const bulletMatch = line.match(/^\s*(?:-|\u2022)\s+(.*)$/);
    if (bulletMatch) {
      const items = [];
      while (i < lines.length) {
        const m = lines[i].match(/^\s*(?:-|\u2022)\s+(.*)$/);
        if (!m) break;
        items.push(m[1]);
        i++;
      }
      blocks.push(
        <ul key={`ul-${i}`} className="list-disc pl-6 mt-1 mb-2">
          {items.map((t, idx) => (
            <li key={idx} className="text-sm text-gray-800 dark:text-slate-100">
              {renderInlineMarkdown(t)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // Normal paragraph (keep empty lines as spacing)
    if (line.trim() === "") {
      blocks.push(<div key={`sp-${i}`} className="h-2" />);
      i++;
      continue;
    }

    blocks.push(
      <p key={`p-${i}`} className="mb-1 text-sm text-gray-800 dark:text-slate-100">
        {renderInlineMarkdown(line)}
      </p>
    );
    i++;
  }

  const isUser = role === "user";
  const ts = formatTs(timestamp);
  return (
    <div className={`flex w-full flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 ${
          isUser
            ? "rounded-tr-sm bg-[#d9fdd3] dark:bg-emerald-900/50"
            : "rounded-tl-sm bg-white shadow-sm dark:bg-slate-800"
        }`}
      >
        {blocks}
      </div>
      {ts ? (
        <span className="px-1 text-[10px] text-gray-400 dark:text-slate-500">{ts}</span>
      ) : null}
    </div>
  );
}

