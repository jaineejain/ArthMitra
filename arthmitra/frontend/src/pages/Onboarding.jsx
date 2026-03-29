import React, { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import ChatBubble from "../components/ChatBubble.jsx";
import TypingIndicator from "../components/TypingIndicator.jsx";
import { clearModuleChat, completeOnboarding, fetchChatHistory, sendMessage } from "../services/api.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function Onboarding() {
  const navigate = useNavigate();
  const { userId } = useAuth();

  const [messages, setMessages] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [input, setInput] = useState("");
  const [loadingChat, setLoadingChat] = useState(false);
  const [loadingScore, setLoadingScore] = useState(false);
  const messagesEndRef = useRef(null);

  const refreshHistory = useCallback(async () => {
    setHistoryLoading(true);
    const r = await fetchChatHistory("onboarding");
    setHistoryLoading(false);
    if (r.error) {
      toast.error("Could not load onboarding chat");
      return;
    }
    const list = r.data?.messages || [];
    setMessages(
      list.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        created_at: m.created_at,
      }))
    );
  }, []);

  useEffect(() => {
    refreshHistory();
  }, [refreshHistory]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loadingChat, loadingScore]);

  async function handleClear() {
    const ok = window.confirm("Clear onboarding chat and restart?");
    if (!ok) return;
    const r = await clearModuleChat("onboarding");
    if (r.error) {
      toast.error("Could not clear");
      return;
    }
    toast.success("Chat cleared");
    await refreshHistory();
  }

  async function handleSend() {
    if (!userId) return;
    const text = String(input || "").trim();
    if (!text || loadingChat || loadingScore) return;

    const historyForApi = messages.slice();
    const userMessage = { role: "user", content: text };
    setInput("");
    setLoadingChat(true);

    try {
      const res = await sendMessage(text, "onboarding", historyForApi);
      if (res.error) {
        toast.error("Send failed — try again");
        return;
      }
      const assistant = res?.data?.response || "Thanks—one more step.";
      const finalMessages = [...historyForApi, userMessage, { role: "assistant", content: assistant }];
      const userCountNext = finalMessages.filter((m) => m.role === "user").length;

      await refreshHistory();

      if (userCountNext >= 8) {
        setLoadingScore(true);
        await completeOnboarding(finalMessages);
        navigate("/dashboard");
      }
    } finally {
      setLoadingChat(false);
      setLoadingScore(false);
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-[#e5ddd5] dark:bg-slate-950">
      <div className="sticky top-0 z-10 border-b border-white/30 bg-[#e5ddd5] p-4 dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-2">
          <div>
            <div className="text-lg font-bold text-gray-800 dark:text-white">ArthMitra Onboarding</div>
            <div className="mt-1 text-xs text-gray-600 dark:text-slate-400">Complete in about 5 minutes</div>
          </div>
          <button
            type="button"
            onClick={handleClear}
            className="rounded-full border border-gray-300 bg-white/80 px-3 py-1 text-xs font-semibold text-gray-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
          >
            Clear chat
          </button>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        <div className="mx-auto w-full max-w-3xl">
          {historyLoading ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="h-14 animate-pulse rounded-2xl bg-white/50 dark:bg-slate-800/80" />
              ))}
            </div>
          ) : null}
          {!historyLoading &&
            messages.map((m, idx) => (
              <div key={m.id || idx} className="mb-3">
                <ChatBubble role={m.role} content={m.content} timestamp={m.created_at} />
              </div>
            ))}
          {loadingChat ? (
            <div className="mt-2">
              <TypingIndicator />
            </div>
          ) : null}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {loadingScore ? (
        <div className="p-4">
          <div className="mx-auto max-w-3xl rounded-2xl border border-gray-200 bg-white/90 p-4 backdrop-blur dark:border-slate-700 dark:bg-slate-900/90">
            <div className="flex items-center gap-3">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-green-600 border-t-transparent" />
              <div>
                <div className="text-sm font-semibold text-gray-900 dark:text-white">Calculating your Money Health Score...</div>
                <div className="mt-1 text-xs text-gray-600 dark:text-slate-400">Just a moment.</div>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      <div className="rounded-t-3xl border-t border-gray-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-3xl items-center gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSend();
            }}
            className="flex-1 rounded-2xl border border-gray-200 bg-white px-4 py-3 outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-white"
            placeholder="Type your answer..."
            disabled={loadingChat || loadingScore}
          />
          <button
            type="button"
            disabled={loadingChat || loadingScore}
            onClick={handleSend}
            className={`rounded-2xl px-5 py-3 font-semibold ${
              loadingChat || loadingScore ? "cursor-not-allowed bg-gray-200 text-gray-500" : "bg-[#16a34a] text-white"
            }`}
          >
            {loadingChat ? "Sending…" : "Send"}
          </button>
        </div>
        <div className="mx-auto mt-2 max-w-3xl text-xs text-gray-500 dark:text-slate-400">
          Tip: Answer with numbers if possible (e.g., ₹85000).
        </div>
      </div>
    </div>
  );
}
