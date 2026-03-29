import React, { useState } from "react";
import { motion } from "framer-motion";

const item = {
  hidden: { opacity: 0, y: 6 },
  show: (i) => ({ opacity: 1, y: 0, transition: { delay: i * 0.04 } }),
};

function Section({ title, children, className = "" }) {
  if (!children) return null;
  return (
    <motion.div
      custom={0}
      variants={item}
      className={`rounded-xl border border-slate-700/80 bg-slate-900/50 p-3 text-sm text-slate-300 ${className}`}
    >
      <div className="mb-1 text-xs font-bold text-slate-200">{title}</div>
      <div className="whitespace-pre-wrap leading-relaxed">{children}</div>
    </motion.div>
  );
}

export default function StructuredMessage({ data }) {
  const [openWhy, setOpenWhy] = useState(false);
  if (!data) return null;

  const modes = data.modes || {};
  const steps = data.action_steps || [];
  const insights = data.insights || [];
  const alternatives = data.alternative_options || [];
  const lang = data.response_language_used || "—";

  return (
    <motion.div
      className="space-y-3 text-left"
      initial="hidden"
      animate="show"
      variants={{ show: { transition: { staggerChildren: 0.05 } } }}
    >
      <motion.div
        custom={0}
        variants={item}
        className="rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-slate-900/90 to-slate-950/90 p-4 shadow-lg backdrop-blur"
      >
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="rounded-full bg-cyan-500/15 px-2 py-0.5 font-semibold text-cyan-300">
            {data.domain || "advisor"}
          </span>
          <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-amber-200">
            confidence: {data.confidence || "medium"}
          </span>
          <span className="rounded-full border border-slate-600 px-2 py-0.5 text-slate-300">🌐 {lang}</span>
        </div>
        {data.clarifying_question ? (
          <div className="mt-3 rounded-xl border border-amber-500/40 bg-amber-950/25 p-3 text-sm text-amber-100">
            <span className="font-semibold">Quick check — </span>
            {data.clarifying_question}
          </div>
        ) : null}
        <div className="mt-3">
          <div className="text-xs font-bold text-emerald-300/90">✅ Quick Summary</div>
          <p className="mt-1 text-base font-medium leading-relaxed whitespace-pre-wrap text-slate-100">{data.answer}</p>
        </div>
      </motion.div>

      {data.key_numbers ? (
        <Section title="📊 Key Numbers">{data.key_numbers}</Section>
      ) : null}

      {data.analysis ? <Section title="📈 Analysis">{data.analysis}</Section> : null}

      {data.explanation ? (
        <motion.div
          custom={1}
          variants={item}
          className="rounded-xl border border-slate-700/80 bg-slate-900/50 p-3 text-sm text-slate-300"
        >
          <span className="font-semibold text-slate-200">Why (detail) — </span>
          <span className="whitespace-pre-wrap">{data.explanation}</span>
        </motion.div>
      ) : null}

      <motion.div custom={2} variants={item} className="grid gap-3 md:grid-cols-3">
        {["safe", "balanced", "growth"].map((k) => (
          <div
            key={k}
            className="rounded-xl border border-slate-700/60 bg-slate-900/40 p-3 text-sm text-slate-300"
          >
            <div className="mb-1 text-xs font-bold uppercase tracking-wide text-amber-400/90">{k}</div>
            <p>{modes[k] || "—"}</p>
          </div>
        ))}
      </motion.div>

      {data.example ? (
        <motion.div
          custom={3}
          variants={item}
          className="rounded-xl border border-violet-500/30 bg-violet-950/20 p-3 text-sm text-violet-100"
        >
          <span className="font-semibold">4. Example — </span>
          {data.example}
        </motion.div>
      ) : null}

      {data.recommendation ? (
        <motion.div
          custom={4}
          variants={item}
          className="rounded-xl border border-emerald-500/25 bg-emerald-950/30 p-3 text-sm text-emerald-100"
        >
          <span className="font-semibold">Top takeaway — </span>
          {data.recommendation}
        </motion.div>
      ) : null}

      {steps.length > 0 ? (
        <motion.div
          custom={7}
          variants={item}
          className="rounded-xl border border-slate-600/50 bg-slate-900/60 p-3"
        >
          <div className="text-xs font-bold text-slate-200">🚀 Action Plan</div>
          <ol className="mt-2 list-inside list-decimal space-y-1 text-sm text-slate-200">
            {steps.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ol>
        </motion.div>
      ) : null}

      {alternatives.length > 0 ? (
        <motion.div
          custom={6}
          variants={item}
          className="rounded-xl border border-violet-500/25 bg-violet-950/25 p-3"
        >
          <div className="text-xs font-bold text-violet-200">🔄 Alternative Options</div>
          <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-slate-200">
            {alternatives.map((x, i) => (
              <li key={i}>{x}</li>
            ))}
          </ul>
        </motion.div>
      ) : null}

      {data.assumptions ? (
        <Section title="⚠️ Assumptions" className="border-orange-500/25 bg-orange-950/15 text-orange-50">
          {data.assumptions}
        </Section>
      ) : null}

      {data.risk_notes ? (
        <motion.div
          custom={5}
          variants={item}
          className="rounded-xl border border-orange-500/30 bg-orange-950/20 p-3 text-sm text-orange-100"
        >
          <span className="font-semibold">⚠️ Risk / disclaimer — </span>
          {data.risk_notes}
        </motion.div>
      ) : null}

      {data.pro_tip ? (
        <motion.div
          custom={6}
          variants={item}
          className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-3 text-sm text-amber-100"
        >
          <div className="text-xs font-bold text-amber-200">💡 Pro Tip</div>
          <p className="mt-2 whitespace-pre-wrap leading-relaxed">{data.pro_tip}</p>
        </motion.div>
      ) : null}

      {insights.length > 0 ? (
        <motion.div
          custom={6}
          variants={item}
          className="rounded-xl border border-cyan-500/20 bg-cyan-950/20 p-3"
        >
          <div className="text-xs font-bold uppercase text-cyan-300">💡 More insights</div>
          <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-slate-200">
            {insights.map((x, i) => (
              <li key={i}>{x}</li>
            ))}
          </ul>
        </motion.div>
      ) : null}

      {data.why_this_answer ? (
        <motion.div custom={8} variants={item}>
          <button
            type="button"
            onClick={() => setOpenWhy(!openWhy)}
            className="text-sm font-semibold text-cyan-400 hover:text-cyan-300"
          >
            {openWhy ? "▼" : "▶"} Why this answer
          </button>
          {openWhy ? (
            <p className="mt-2 rounded-lg bg-slate-900/80 p-3 text-sm text-slate-400">{data.why_this_answer}</p>
          ) : null}
        </motion.div>
      ) : null}
    </motion.div>
  );
}
