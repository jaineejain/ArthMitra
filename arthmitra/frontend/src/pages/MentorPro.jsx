import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import ChatSidebar, { loadSessions, saveSessions } from "../components/mentor/ChatSidebar.jsx";
import StructuredMessage from "../components/mentor/StructuredMessage.jsx";
import NotificationBell from "../components/mentor/NotificationBell.jsx";
import { mentorChat, simulateWealth } from "../services/api.js";
import { useAuth } from "../context/AuthContext.jsx";

const WELCOME_KEY = "mentor_show_welcome_v1";
const NAME_KEY = "mentor_display_name";
const GOALS_KEY = "mentor_goals_v1";
const CONTEXT_KEY = "mentor_context_v1";
const FLOW_KEY = "mentor_flow_v1";

/** Maps UI flow label → backend planner_section (CA section-scoped questions) */
const FLOW_TO_PLANNER = {
  "General chat": "general_finance",
  FIRE: "general_finance",
  "Money Health": "general_finance",
  Tax: "tax",
  Invest: "investment",
  "Couple / Family": "couple_family",
  "Debt / Loan": "debt_loan",
};

function uid() {
  return crypto.randomUUID ? crypto.randomUUID() : `s_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function loadGoals() {
  try {
    const g = localStorage.getItem(GOALS_KEY);
    return g ? JSON.parse(g) : [];
  } catch {
    return [];
  }
}

function saveGoals(g) {
  localStorage.setItem(GOALS_KEY, JSON.stringify(g));
}

function loadContext() {
  try {
    const c = localStorage.getItem(CONTEXT_KEY);
    return c ? JSON.parse(c) : {};
  } catch {
    return {};
  }
}

function saveContext(c) {
  localStorage.setItem(CONTEXT_KEY, JSON.stringify(c));
}

/** Pull income-like numbers from free text */
function extractContextFromMessage(text) {
  const t = String(text);
  const ctx = { ...loadContext() };
  const lakh = t.match(/(\d+(?:\.\d+)?)\s*l(?:akh)?/i);
  const k = t.match(/(\d+)\s*k\b/i);
  const rupee = t.match(/₹\s*([\d,]+)/);
  const plain = t.match(/\b(\d{4,7})\b/);
  let monthly = null;
  if (lakh) monthly = Math.round(parseFloat(lakh[1]) * 100000);
  else if (k) monthly = Math.round(parseInt(k[1], 10) * 1000);
  else if (rupee) monthly = parseInt(rupee[1].replace(/,/g, ""), 10);
  else if (plain) monthly = parseInt(plain[1], 10);
  if (monthly && monthly >= 5000 && monthly <= 5000000) {
    ctx.income_monthly = monthly;
  }
  const age = t.match(/\bage\s*(\d{2})\b/i) || t.match(/\b(\d{2})\s*years?\s*old\b/i);
  if (age) ctx.age = parseInt(age[1], 10);
  saveContext(ctx);
  return ctx;
}

const SIP_Q = /invest\s*₹?\s*([\d,]+)\s*(?:monthly|per month|\/month)?\s*for\s*(\d+)\s*years?/i;
const SIP_Q2 = /(\d+)\s*monthly.*(\d+)\s*years?/i;

function TypingDots() {
  return (
    <div className="flex items-center gap-1.5 rounded-2xl border border-slate-700 bg-slate-900 px-4 py-3">
      <span className="h-2 w-2 animate-bounce rounded-full bg-cyan-400 [animation-delay:0ms]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-cyan-400 [animation-delay:150ms]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-cyan-400 [animation-delay:300ms]" />
      <span className="ml-2 text-sm text-slate-400">Thinking…</span>
    </div>
  );
}

export default function MentorPro() {
  const { userId } = useAuth();
  const [mobileSidebar, setMobileSidebar] = useState(false);
  const [sessionId, setSessionId] = useState(() => localStorage.getItem("mentor_active_session") || uid());
  const [search, setSearch] = useState("");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sip, setSip] = useState(10000);
  const [years, setYears] = useState(10);
  const [fv, setFv] = useState(null);
  const [showWelcome, setShowWelcome] = useState(() => localStorage.getItem(WELCOME_KEY) !== "0");
  const [displayName, setDisplayName] = useState(() => localStorage.getItem(NAME_KEY) || "");
  const [language, setLanguage] = useState(() => localStorage.getItem("mentor_lang") || "hinglish");
  const [expertMode, setExpertMode] = useState(() => localStorage.getItem("mentor_expert") === "1");
  const [flowLabel, setFlowLabel] = useState(() => localStorage.getItem(FLOW_KEY) || "General chat");
  const [goals, setGoals] = useState(loadGoals);
  const [context, setContext] = useState(loadContext);
  const [sipPreview, setSipPreview] = useState(null);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    localStorage.setItem("mentor_lang", language);
  }, [language]);
  useEffect(() => {
    localStorage.setItem("mentor_expert", expertMode ? "1" : "0");
  }, [expertMode]);

  const persistSession = useCallback(
    (msgs, titleGuess) => {
      const sessions = loadSessions();
      const idx = sessions.findIndex((s) => s.id === sessionId);
      const title =
        titleGuess ||
        (msgs.find((m) => m.role === "user")?.content || "New conversation").slice(0, 42);
      const row = { id: sessionId, title, updated: Date.now(), messages: msgs };
      if (idx >= 0) sessions[idx] = row;
      else sessions.unshift(row);
      sessions.sort((a, b) => b.updated - a.updated);
      saveSessions(sessions);
      localStorage.setItem("mentor_active_session", sessionId);
      window.dispatchEvent(new Event("mentor-chats-updated"));
    },
    [sessionId]
  );

  const defaultWelcomeMsg = useCallback(
    () => [
      {
        role: "assistant",
        content: `Namaste${displayName ? ` **${displayName}**` : ""} — I'm **ArthMitra**, your AI money coach. Ask anything or use the chips below. I'll give you a clear summary, key numbers (approximate where needed), action plan, alternatives, and assumptions — India-first, practical.`,
      },
    ],
    [displayName]
  );

  useEffect(() => {
    const sessions = loadSessions();
    const s = sessions.find((x) => x.id === sessionId);
    if (s?.messages?.length) setMessages(s.messages);
    else setMessages(defaultWelcomeMsg());
  }, [sessionId, defaultWelcomeMsg]);

  function clearChatMessagesForSession(id) {
    const sessions = loadSessions();
    const idx = sessions.findIndex((s) => s.id === id);
    const fresh = defaultWelcomeMsg();
    if (idx >= 0) {
      sessions[idx] = { ...sessions[idx], messages: fresh, updated: Date.now() };
      saveSessions(sessions);
    }
    if (id === sessionId) setMessages(fresh);
    window.dispatchEvent(new Event("mentor-chats-updated"));
  }

  function clearCurrentChat() {
    if (!window.confirm("Clear all messages in this chat?")) return;
    clearChatMessagesForSession(sessionId);
  }

  async function maybeAppendSipMath(userText) {
    let m = userText.match(SIP_Q);
    if (!m) m = userText.match(SIP_Q2);
    if (!m) return;
    const monthly = parseInt(String(m[1]).replace(/,/g, ""), 10);
    const yrs = parseInt(m[2], 10);
    if (!monthly || !yrs) return;
    const r = await simulateWealth({ monthly_sip_rupees: monthly, years: yrs, annual_return: 0.12 });
    if (r.data?.success) {
      setSipPreview({
        monthly,
        years: yrs,
        fv: r.data.future_value_rupees,
      });
    }
  }

  async function onSend(text) {
    const t = String(text || "").trim();
    if (!t || loading) return;
    extractContextFromMessage(t);
    setContext(loadContext());
    void maybeAppendSipMath(t);

    const next = [...messages, { role: "user", content: t }];
    setMessages(next);
    setInput("");
    setLoading(true);
    const hist = next.slice(0, -1).map(({ role, content }) => ({ role, content }));
    const res = await mentorChat(t, hist, {
      language,
      expert_mode: expertMode,
      auto_detect_language: language !== "english",
      display_name: displayName || null,
      professional_ca: language === "english",
      planner_section: FLOW_TO_PLANNER[flowLabel] || "general_finance",
    });
    setLoading(false);
    if (res.error || !res.data?.success) {
      const errMsg =
        res.data?.error ||
        res.error ||
        "Hmm, I didn’t fully get that — can you rephrase once with a bit more detail?";
      const final = [...next, { role: "assistant", content: errMsg }];
      setMessages(final);
      persistSession(final, t);
      return;
    }
    const data = res.data.data;
    const assistantText = data?.answer || "Here’s your structured plan below.";
    const final = [...next, { role: "assistant", content: assistantText, structured: data }];
    setMessages(final);
    persistSession(final, t);
  }

  async function refreshSim() {
    const r = await simulateWealth({ monthly_sip_rupees: sip, years, annual_return: 0.12 });
    if (r.data?.success) setFv(r.data.future_value_rupees);
  }

  useEffect(() => {
    refreshSim();
  }, [sip, years]);

  function newChat() {
    const id = uid();
    setSessionId(id);
    setMessages(defaultWelcomeMsg());
    localStorage.setItem("mentor_active_session", id);
  }

  function startWelcome(name) {
    const n = String(name || "").trim() || "there";
    localStorage.setItem(NAME_KEY, n);
    localStorage.setItem(WELCOME_KEY, "0");
    setDisplayName(n);
    setShowWelcome(false);
  }

  function addGoal() {
    const g = window.prompt("Goal (e.g. Buy house in 5 years, ₹20L down payment)");
    if (!g) return;
    const next = [...goals, { id: uid(), text: g, created: Date.now() }];
    setGoals(next);
    saveGoals(next);
  }

  const chips = [
    { label: "Start FIRE Plan 🔥", flow: "FIRE", send: "I want to plan FIRE — guide me step by step." },
    { label: "Check Money Health 📊", flow: "Money Health", send: "Check my money health — what metrics matter first?" },
    { label: "Save Tax 💰", flow: "Tax", send: "Help me save tax this year — old vs new regime and deductions." },
    { label: "Invest Better 📈", flow: "Invest", send: "How should I invest better — SIP, allocation, and mistakes to avoid?" },
    { label: "Family plan 👪", flow: "Couple / Family", send: "We are planning finances as a couple — income, goals, and how to split investments." },
    { label: "Debt / loan 📉", flow: "Debt / Loan", send: "I want help with loans — interest rate, EMI, and prepayment strategy." },
  ];

  const chipSend = (c) => {
    setFlowLabel(c.flow);
    localStorage.setItem(FLOW_KEY, c.flow);
    onSend(c.send);
  };

  const efMonths = context.ef_months ?? 3;
  const healthDims = [
    { k: "Emergency", v: context.income_monthly != null ? Math.min(100, Math.round(efMonths * 20)) : null },
    { k: "Invest", v: 55 },
    { k: "Debt", v: 70 },
    { k: "Insurance", v: 45 },
    { k: "Retirement", v: 50 },
  ];

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden bg-[#070b14] text-slate-100">
      <AnimatePresence>
        {showWelcome ? (
          <motion.div
            className="fixed inset-0 z-[100] flex items-center justify-center bg-[#050810]/95 p-4 backdrop-blur-md"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              initial={{ scale: 0.96, y: 10 }}
              animate={{ scale: 1, y: 0 }}
              className="max-w-lg rounded-3xl border border-cyan-500/20 bg-gradient-to-b from-slate-900 to-slate-950 p-8 shadow-2xl"
            >
              <h2 className="text-2xl font-bold text-white">
                👋 Welcome{displayName ? ` ${displayName}` : ""}
              </h2>
              <p className="mt-2 text-slate-400">
                I’m <span className="text-cyan-300">ArthMitra</span> — your personal AI financial coach. Let’s build your
                future step by step 🚀
              </p>
              <input
                placeholder="Your first name (optional)"
                className="mt-4 w-full rounded-xl border border-slate-600 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-cyan-500/50"
                onKeyDown={(e) => {
                  if (e.key === "Enter") startWelcome(e.target.value);
                }}
                id="welcome-name"
              />
              <div className="mt-4 grid grid-cols-2 gap-2">
                {chips.map((c) => (
                  <button
                    key={c.flow}
                    type="button"
                    className="rounded-xl border border-slate-700 bg-slate-900 py-3 text-sm font-medium hover:border-cyan-500/40"
                    onClick={() => {
                      const el = document.getElementById("welcome-name");
                      startWelcome(el?.value || "");
                      setTimeout(() => chipSend(c), 100);
                    }}
                  >
                    {c.label}
                  </button>
                ))}
              </div>
              <button
                type="button"
                className="mt-4 w-full rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 py-3 text-sm font-bold text-white"
                onClick={() => {
                  const el = document.getElementById("welcome-name");
                  startWelcome(el?.value || "");
                }}
              >
                Enter app
              </button>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 px-3 py-2 md:px-4">
        <div>
          <h1 className="bg-gradient-to-r from-cyan-400 to-amber-300 bg-clip-text text-lg font-bold text-transparent md:text-xl">
            AI Money Mentor Pro
          </h1>
          <p className="text-[10px] text-slate-500 md:text-xs">
            Structured · India-first · {flowLabel}
            {language === "english" ? " · CA-style (professional English)" : ""}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="rounded-lg border border-slate-600 bg-slate-900 px-2 py-1.5 text-xs text-slate-200"
          >
            <option value="english">English</option>
            <option value="hindi">Hindi</option>
            <option value="hinglish">Hinglish</option>
            <option value="marathi">Marathi</option>
            <option value="gujarati">Gujarati</option>
          </select>
          <label className="flex cursor-pointer items-center gap-1 text-xs text-slate-400">
            <input type="checkbox" checked={expertMode} onChange={(e) => setExpertMode(e.target.checked)} />
            Expert
          </label>
          <NotificationBell onPickAlert={(prompt) => onSend(prompt)} />
          <button
            type="button"
            onClick={clearCurrentChat}
            className="rounded-lg border border-slate-600 px-2 py-1.5 text-xs text-slate-300 hover:bg-slate-800"
            title="Clear this chat"
          >
            Clear chat
          </button>
          <Link to="/dashboard" className="rounded-lg border border-slate-600 px-2 py-1.5 text-xs text-slate-300 hover:bg-slate-800">
            Dashboard
          </Link>
          <button
            type="button"
            className="rounded-lg border border-slate-600 px-2 py-1.5 text-xs text-slate-300 hover:bg-slate-800 md:hidden"
            onClick={() => setMobileSidebar((v) => !v)}
            aria-label="Toggle chats"
          >
            Chats
          </button>
        </div>
      </header>

      <div className="relative flex min-h-0 flex-1">
        {mobileSidebar ? (
          <div
            className="fixed inset-0 z-40 bg-black/60 md:hidden"
            role="presentation"
            onClick={() => setMobileSidebar(false)}
          />
        ) : null}
        <div
          className={`${
            mobileSidebar ? "fixed inset-y-0 left-0 z-50 w-[min(100%,18rem)] shadow-2xl md:relative md:z-auto md:w-auto md:shadow-none" : "hidden"
          } md:flex md:h-full`}
        >
          <ChatSidebar
            activeId={sessionId}
            onSelect={(id) => {
              setSessionId(id);
              setMobileSidebar(false);
            }}
            onNewChat={() => {
              newChat();
              setMobileSidebar(false);
            }}
            onClearChatMessages={clearChatMessagesForSession}
            search={search}
            onSearchChange={setSearch}
          />
        </div>

        <main className="flex min-w-0 flex-1 flex-col">
          <div className="grid min-h-0 flex-1 gap-3 overflow-hidden p-2 md:grid-cols-[1fr_300px] md:p-4">
            <div className="flex min-h-0 flex-col rounded-2xl border border-slate-800 bg-slate-950/50">
              <div className="border-b border-slate-800 p-2 md:p-3">
                <div className="mb-2 flex flex-wrap items-center gap-2 text-[10px] text-slate-500 md:text-xs">
                  <span className="rounded-full bg-slate-800 px-2 py-0.5">Session memory</span>
                  <span className="text-cyan-400/90">{flowLabel}</span>
                  <span className="h-1 flex-1 min-w-[40px] max-w-[120px] overflow-hidden rounded-full bg-slate-800">
                    <span
                      className="block h-full rounded-full bg-gradient-to-r from-cyan-500 to-amber-400"
                      style={{ width: `${Math.min(100, (messages.filter((m) => m.role === "user").length / 8) * 100)}%` }}
                    />
                  </span>
                </div>
                {(context.income_monthly || context.age) && (
                  <div className="mb-2 flex flex-wrap gap-2">
                    {context.income_monthly ? (
                      <span className="rounded-lg border border-emerald-500/30 bg-emerald-950/30 px-2 py-1 text-[10px] text-emerald-200 md:text-xs">
                        Income ~ ₹{context.income_monthly.toLocaleString("en-IN")}/mo
                      </span>
                    ) : null}
                    {context.age ? (
                      <span className="rounded-lg border border-slate-600 bg-slate-900 px-2 py-1 text-[10px] md:text-xs">
                        Age ~ {context.age}
                      </span>
                    ) : null}
                  </div>
                )}
                <div className="flex flex-wrap gap-2">
                  {chips.map((c) => (
                    <button
                      key={c.flow}
                      type="button"
                      onClick={() => chipSend(c)}
                      disabled={loading}
                      className="rounded-full border border-cyan-500/30 bg-slate-900/80 px-2 py-1 text-[10px] text-cyan-200 hover:bg-slate-800 disabled:opacity-50 md:px-3 md:text-xs"
                    >
                      {c.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex-1 space-y-3 overflow-y-auto p-2 md:space-y-4 md:p-4">
                {messages.map((m, i) => (
                  <div key={i} className={`flex gap-2 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div className="order-2 max-w-[90%] md:order-none">
                      <div
                        className={`rounded-2xl px-3 py-2 text-sm md:px-4 md:py-3 ${
                          m.role === "user"
                            ? "bg-gradient-to-br from-emerald-600 to-emerald-800 text-white"
                            : "border border-slate-700 bg-slate-900/80 text-slate-100"
                        }`}
                      >
                        {m.role === "assistant" && !m.structured ? (
                          <div className="flex items-start gap-2">
                            <span className="text-lg leading-none">🤖</span>
                            <p className="whitespace-pre-wrap">{m.content}</p>
                          </div>
                        ) : m.role === "user" ? (
                          <div className="flex items-start gap-2">
                            <p className="flex-1 whitespace-pre-wrap">{m.content}</p>
                            <span className="text-lg">👤</span>
                          </div>
                        ) : null}
                        {m.structured ? <StructuredMessage data={m.structured} /> : null}
                      </div>
                    </div>
                  </div>
                ))}
                {sipPreview ? (
                  <div className="rounded-xl border border-violet-500/30 bg-violet-950/20 p-3 text-sm text-violet-100">
                    <div className="font-semibold">📊 Quick calc</div>
                    <div className="mt-1 text-xs text-violet-200/90">
                      ₹{sipPreview.monthly.toLocaleString("en-IN")}/mo × {sipPreview.years} yrs @ ~12% illustrative → ≈ ₹
                      {Math.round(sipPreview.fv).toLocaleString("en-IN")}
                    </div>
                    <button type="button" className="mt-2 text-xs text-violet-300 underline" onClick={() => setSipPreview(null)}>
                      Dismiss
                    </button>
                  </div>
                ) : null}
                {loading ? (
                  <div className="flex justify-start pl-1">
                    <TypingDots />
                  </div>
                ) : null}
                <div ref={endRef} />
              </div>

              <div className="safe-pb sticky bottom-0 border-t border-slate-800 bg-slate-950/95 p-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] md:p-3">
                <div className="flex gap-2">
                  <button
                    type="button"
                    title="Voice input (browser)"
                    className="rounded-xl border border-slate-600 px-2 text-lg text-slate-300 hover:bg-slate-800"
                    onClick={() => {
                      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
                      if (!SR) {
                        alert("Voice not supported in this browser.");
                        return;
                      }
                      const r = new SR();
                      r.lang = "hi-IN";
                      r.onresult = (ev) => {
                        const t = ev.results[0][0].transcript;
                        setInput((prev) => (prev ? `${prev} ${t}` : t));
                      };
                      r.start();
                    }}
                  >
                    🎤
                  </button>
                  <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && onSend(input)}
                    disabled={loading}
                    placeholder="Ask anything… (try: mera salary 50k hai)"
                    className="flex-1 rounded-xl border border-slate-700 bg-slate-900 px-3 py-2.5 text-sm outline-none focus:border-cyan-500/40 disabled:opacity-50 md:px-4 md:py-3"
                  />
                  <button
                    type="button"
                    disabled={loading}
                    onClick={() => onSend(input)}
                    className="rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50 md:px-6"
                  >
                    Send
                  </button>
                </div>
              </div>
            </div>

            <aside className="hidden min-h-0 space-y-3 overflow-y-auto rounded-2xl border border-slate-800 bg-slate-950/60 p-3 md:block">
              <div>
                <h3 className="text-xs font-bold uppercase text-amber-200">Money pulse</h3>
                <div className="mt-2 space-y-2">
                  {healthDims.map((d) => (
                    <div key={d.k}>
                      <div className="flex justify-between text-[10px] text-slate-400">
                        <span>{d.k}</span>
                        <span>{d.v != null ? `${d.v}%` : "—"}</span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className={`h-full rounded-full ${
                            (d.v || 0) >= 70 ? "bg-emerald-500" : (d.v || 0) >= 45 ? "bg-amber-500" : "bg-red-500"
                          }`}
                          style={{ width: `${d.v ?? 15}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                <p className="mt-2 text-[10px] text-slate-600">Illustrative bars for demo; connect to real MHS API next.</p>
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase text-cyan-200">Goals</h3>
                  <button type="button" onClick={addGoal} className="text-[10px] text-cyan-400 hover:underline">
                    + Add
                  </button>
                </div>
                <ul className="mt-2 space-y-1 text-xs text-slate-300">
                  {goals.map((g) => (
                    <li key={g.id} className="rounded-lg border border-slate-700 bg-slate-900/50 px-2 py-1">
                      {g.text}
                    </li>
                  ))}
                  {goals.length === 0 ? <li className="text-slate-500">No goals yet</li> : null}
                </ul>
              </div>

              <div>
                <h3 className="text-sm font-bold text-amber-200">Future wealth</h3>
                <p className="mt-1 text-[10px] text-slate-500">SIP → FV @ ~12% (not guaranteed)</p>
                <label className="mt-2 block text-[10px] text-slate-400">
                  ₹{sip.toLocaleString("en-IN")}/mo
                  <input
                    type="range"
                    min={1000}
                    max={100000}
                    step={500}
                    value={sip}
                    onChange={(e) => setSip(Number(e.target.value))}
                    className="mt-1 w-full"
                  />
                </label>
                <label className="mt-2 block text-[10px] text-slate-400">
                  {years} yrs
                  <input
                    type="range"
                    min={5}
                    max={30}
                    step={1}
                    value={years}
                    onChange={(e) => setYears(Number(e.target.value))}
                    className="mt-1 w-full"
                  />
                </label>
                {fv != null ? (
                  <p className="mt-2 text-base font-semibold text-cyan-300">≈ ₹{Math.round(fv).toLocaleString("en-IN")}</p>
                ) : null}
              </div>
            </aside>
          </div>
        </main>
      </div>
    </div>
  );
}
