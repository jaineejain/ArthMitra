import React, { useMemo, useState } from "react";

const STORAGE_KEY = "mentor_chats_v2";

function loadSessions() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const p = JSON.parse(raw);
    return Array.isArray(p) ? p : [];
  } catch {
    return [];
  }
}

function saveSessions(sessions) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

export default function ChatSidebar({
  activeId,
  onSelect,
  onNewChat,
  onClearChatMessages,
  search,
  onSearchChange,
}) {
  const [sessions, setSessions] = useState(loadSessions);

  const filtered = useMemo(() => {
    const q = (search || "").toLowerCase();
    if (!q) return sessions;
    return sessions.filter((s) => (s.title || "").toLowerCase().includes(q) || (s.id || "").includes(q));
  }, [sessions, search]);

  function removeSession(id, e) {
    e.stopPropagation();
    const next = sessions.filter((s) => s.id !== id);
    setSessions(next);
    saveSessions(next);
    if (id === activeId && next[0]) onSelect(next[0].id);
  }

  function clearAll() {
    if (!window.confirm("Clear all chat history?")) return;
    setSessions([]);
    saveSessions([]);
    onNewChat();
  }

  // expose refresh for parent
  React.useEffect(() => {
    const h = () => setSessions(loadSessions());
    window.addEventListener("mentor-chats-updated", h);
    return () => window.removeEventListener("mentor-chats-updated", h);
  }, []);

  return (
    <aside className="flex h-full w-72 flex-col border-r border-slate-800 bg-slate-950/80">
      <div className="border-b border-slate-800 p-3">
        <input
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search chats..."
          className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-cyan-500/50"
        />
        <div className="mt-2 flex gap-2">
          <button
            type="button"
            onClick={onNewChat}
            className="flex-1 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 py-2 text-sm font-semibold text-white shadow-lg"
          >
            New chat
          </button>
          <button
            type="button"
            onClick={clearAll}
            className="rounded-xl border border-slate-600 px-2 py-2 text-xs text-slate-400 hover:text-white"
          >
            Clear
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto">
        {filtered.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => onSelect(s.id)}
            className={`flex w-full items-start justify-between gap-2 border-b border-slate-800/80 px-3 py-3 text-left text-sm hover:bg-slate-900/80 ${
              s.id === activeId ? "bg-slate-900/90 border-l-2 border-l-cyan-500" : ""
            }`}
          >
            <span className="line-clamp-2 text-slate-200">{s.title || "Untitled"}</span>
            <span className="flex shrink-0 gap-1">
              <span
                role="button"
                tabIndex={0}
                title="Clear messages in this chat"
                onClick={(e) => {
                  e.stopPropagation();
                  onClearChatMessages?.(s.id);
                }}
                className="text-slate-500 hover:text-amber-400"
              >
                ⟲
              </span>
              <span
                role="button"
                tabIndex={0}
                title="Delete chat"
                onClick={(e) => removeSession(s.id, e)}
                className="text-slate-500 hover:text-red-400"
              >
                ×
              </span>
            </span>
          </button>
        ))}
        {filtered.length === 0 ? <div className="p-4 text-center text-xs text-slate-500">No history yet</div> : null}
      </div>
    </aside>
  );
}

export { STORAGE_KEY, loadSessions, saveSessions };
