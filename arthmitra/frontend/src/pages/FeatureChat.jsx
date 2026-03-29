import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import {
  clearModuleChat,
  fetchChatHistory,
  getProfile,
  sendMessage,
  uploadFile,
} from "../services/api.js";
import { useAuth } from "../context/AuthContext.jsx";
import ChatBubble from "../components/ChatBubble.jsx";
import TypingIndicator from "../components/TypingIndicator.jsx";

import FireCard from "../components/ResultCards/FireCard.jsx";
import TaxCard from "../components/ResultCards/TaxCard.jsx";
import MHSCard from "../components/ResultCards/MHSCard.jsx";
import LifeEventCard from "../components/ResultCards/LifeEventCard.jsx";
import MFXrayCard from "../components/ResultCards/MFXrayCard.jsx";
import CoupleCard from "../components/ResultCards/CoupleCard.jsx";

const VALID_FEATURES = new Set(["fire", "tax", "life_event", "mf_xray", "couple", "mhs"]);

const featureTitle = {
  fire: "FIRE Planner",
  tax: "Tax Wizard",
  life_event: "Life Event Advisor",
  mf_xray: "MF Portfolio X-Ray",
  couple: "Couple's Planner",
  mhs: "Money Health",
};

export default function FeatureChat() {
  const { feature } = useParams();
  const navigate = useNavigate();
  const { userId } = useAuth();

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [cardData, setCardData] = useState(null);
  const [cardType, setCardType] = useState(null);
  const [profile, setProfile] = useState(null);
  const [showUpload, setShowUpload] = useState(false);
  const [retryPayload, setRetryPayload] = useState(null);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const headerScore = profile?.financial_profile?.mhs_score ?? 0;

  const refreshHistory = useCallback(async () => {
    if (!feature || !VALID_FEATURES.has(feature)) return;
    setHistoryLoading(true);
    const r = await fetchChatHistory(feature);
    setHistoryLoading(false);
    if (r.error) {
      toast.error(typeof r.error === "string" ? r.error : "Could not load chat history");
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
  }, [feature]);

  useEffect(() => {
    let mounted = true;
    async function loadProfile() {
      if (!userId) return;
      const res = await getProfile(userId);
      if (mounted) setProfile(res.data || null);
    }
    loadProfile();
    return () => {
      mounted = false;
    };
  }, [userId]);

  useEffect(() => {
    refreshHistory();
  }, [refreshHistory]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  const cardRenderer = useMemo(() => {
    return {
      fire: <FireCard data={cardData} />,
      tax: <TaxCard data={cardData} />,
      mhs: <MHSCard data={cardData} />,
      couple: <CoupleCard data={cardData} />,
      life_event: <LifeEventCard data={cardData} />,
      mf_xray: <MFXrayCard data={cardData} />,
    }[cardType];
  }, [cardType, cardData]);

  async function handleClearOrNew() {
    if (!feature) return;
    const ok = window.confirm("Clear this module’s chat and start fresh?");
    if (!ok) return;
    const r = await clearModuleChat(feature);
    if (r.error) {
      toast.error("Could not clear chat");
      return;
    }
    toast.success("Chat cleared");
    await refreshHistory();
    setCardData(null);
    setCardType(null);
    setRetryPayload(null);
  }

  async function handleUploadCams(file) {
    const historyForApi = messages.slice();
    setLoading(true);
    setRetryPayload(null);
    try {
      const up = await uploadFile(file, "cams");
      const portfolioResp = up.data;
      if (up.error) {
        toast.error("Upload failed");
        setLoading(false);
        return;
      }

      const userMsg = { role: "user", content: "Upload CAMS / KFintech statement for MF X-Ray." };
      setMessages([...historyForApi, userMsg]);

      const portfolioJson = JSON.stringify(portfolioResp, null, 2);
      const send = await sendMessage(`PORTFOLIO_JSON:\n${portfolioJson}`, feature, historyForApi);
      if (send.error) {
        toast.error("AI reply failed — tap Retry");
        setRetryPayload({ type: "portfolio", portfolioJson });
        setLoading(false);
        return;
      }
      setRetryPayload(null);
      await refreshHistory();
      setCardData(portfolioResp);
      setCardType("mf_xray");
    } finally {
      setLoading(false);
    }
  }

  async function handleSendMessage(raw) {
    const text = String(raw || "").trim();
    if (!text || loading) return;

    setInput("");
    setCardData(null);
    setCardType(null);
    setLoading(true);

    try {
      const lower = text.toLowerCase();
      const historyForApi = messages.slice();

      if (feature === "mf_xray") {
        if (lower.includes("upload")) {
          setShowUpload(true);
          setRetryPayload(null);
          return;
        }
        if (lower.includes("sample")) {
          const up = await uploadFile(null, "cams");
          const portfolioResp = up.data;
          if (up.error) {
            toast.error("Sample load failed");
            setRetryPayload({ type: "text", text });
            return;
          }
          setCardData(portfolioResp);
          setCardType("mf_xray");
          const portfolioJson = JSON.stringify(portfolioResp, null, 2);
          const send = await sendMessage(`PORTFOLIO_JSON:\n${portfolioJson}`, feature, historyForApi);
          if (send.error) {
            toast.error("AI reply failed — tap Retry");
            setRetryPayload({ type: "text", text });
            return;
          }
          setRetryPayload(null);
          await refreshHistory();
          return;
        }
      }

      const res = await sendMessage(text, feature, historyForApi);
      if (res.error) {
        toast.error("Something went wrong — you can retry.");
        setRetryPayload({ type: "text", text });
        return;
      }
      setRetryPayload(null);
      const newCardData = res?.data?.card_data || null;
      const newCardType = res?.data?.card_type || null;
      setCardData(newCardData);
      setCardType(newCardType);
      await refreshHistory();
    } finally {
      setLoading(false);
    }
  }

  async function handleRetry() {
    if (!retryPayload) return;
    if (retryPayload.type === "text") {
      setInput(retryPayload.text);
      await handleSendMessage(retryPayload.text);
    } else if (retryPayload.type === "portfolio" && retryPayload.portfolioJson) {
      setLoading(true);
      try {
        const send = await sendMessage(`PORTFOLIO_JSON:\n${retryPayload.portfolioJson}`, feature, messages.slice());
        if (send.error) {
          toast.error("Still failing — check network / API");
          return;
        }
        setRetryPayload(null);
        await refreshHistory();
      } finally {
        setLoading(false);
      }
    }
  }

  if (!VALID_FEATURES.has(feature)) {
    return <Navigate to="/dashboard" replace />;
  }

  const title = featureTitle[feature] || "Chat";

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-[#fafaf8] dark:bg-slate-950">
      <div className="sticky top-0 z-10 border-b border-gray-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="font-semibold text-gray-700 dark:text-slate-200 md:hidden"
              onClick={() => navigate("/dashboard")}
              aria-label="Back"
            >
              ←
            </button>
            <div>
              <div className="text-lg font-bold text-gray-900 dark:text-white">{title}</div>
              <div className="mt-1 text-xs text-gray-500 dark:text-slate-400">{feature}</div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={handleClearOrNew}
              className="rounded-full border border-gray-200 px-3 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              Clear chat
            </button>
            <button
              type="button"
              onClick={handleClearOrNew}
              className="rounded-full bg-emerald-600 px-3 py-1 text-xs font-semibold text-white hover:bg-emerald-700"
            >
              New chat
            </button>
            <div className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs font-semibold text-gray-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200">
              MHS: {headerScore}
            </div>
          </div>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto bg-[#e5ddd5] p-4 dark:bg-slate-900">
        <div className="mx-auto w-full max-w-3xl">
          {historyLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-16 animate-pulse rounded-2xl bg-white/60 dark:bg-slate-800/80"
                  style={{ marginLeft: i % 2 ? "auto" : 0, maxWidth: "75%" }}
                />
              ))}
            </div>
          ) : null}
          {!historyLoading &&
            messages.map((m, idx) => (
              <div key={m.id || `${idx}-${m.role}`} className="mb-3">
                <ChatBubble role={m.role} content={m.content} timestamp={m.created_at} />
                {idx === messages.length - 1 && cardRenderer ? <div className="mt-2">{cardRenderer}</div> : null}
              </div>
            ))}

          {loading ? (
            <div className="mt-2">
              <TypingIndicator />
            </div>
          ) : null}

          {retryPayload && !loading ? (
            <div className="mt-4 flex justify-center">
              <button
                type="button"
                onClick={handleRetry}
                className="rounded-full bg-amber-500 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-amber-600"
              >
                Retry last message
              </button>
            </div>
          ) : null}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {feature === "mf_xray" && showUpload ? (
        <div className="px-4 pb-4">
          <div className="mx-auto max-w-3xl rounded-2xl border border-gray-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
            <div className="text-sm font-semibold text-gray-900 dark:text-white">Upload your CAMS/KFintech PDF</div>
            <div className="mt-1 text-xs text-gray-500 dark:text-slate-400">
              On failure, we’ll silently use a sample portfolio.
            </div>
            <div className="mt-3">
              <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf"
                className="block w-full text-sm text-gray-700 dark:text-slate-300"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleUploadCams(f);
                  setShowUpload(false);
                }}
              />
            </div>
            <button
              type="button"
              className="mt-3 text-sm font-semibold text-gray-700 underline dark:text-slate-300"
              onClick={() => setShowUpload(false)}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : null}

      <div className="border-t border-gray-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-3xl items-center gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSendMessage(input);
            }}
            className="flex-1 rounded-2xl border border-gray-200 bg-white px-4 py-3 outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-white"
            placeholder="Type your message..."
            disabled={loading}
          />
          <button
            type="button"
            disabled={loading}
            onClick={() => handleSendMessage(input)}
            className={`rounded-2xl px-5 py-3 font-semibold ${
              loading ? "cursor-not-allowed bg-gray-200 text-gray-500" : "bg-[#16a34a] text-white"
            }`}
          >
            {loading ? "Sending…" : "Send"}
          </button>
        </div>
        <div className="mx-auto mt-2 max-w-3xl text-xs text-gray-500 dark:text-slate-400">
          Tip: For MF X-Ray, type `sample` or `upload`.
        </div>
      </div>
    </div>
  );
}
