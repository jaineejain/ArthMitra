import React, { useEffect, useMemo, useState } from "react";

function ringColor(score1000) {
  const pct = score1000 / 10; // 0-100
  if (pct < 50) return { stroke: "#dc2626", text: "#b91c1c", bg: "bg-red-50" };
  if (pct < 70) return { stroke: "#d97706", text: "#b45309", bg: "bg-amber-50" };
  return { stroke: "#16a34a", text: "#15803d", bg: "bg-green-50" };
}

function miniColor(score100) {
  if (score100 < 50) return "#dc2626";
  if (score100 < 70) return "#d97706";
  return "#16a34a";
}

export default function KarmaScore({ data }) {
  const total = Number(data?.total || 0);
  const dims = data?.dimensions || {};
  const weakest = data?.weakest || "investment";
  const percentile = data?.percentile || "Top 20%";

  const target = Math.max(0, Math.min(1000, total));
  const [animated, setAnimated] = useState(0);

  const radius = 34;
  const strokeWidth = 8;
  const normalizedRadius = radius - strokeWidth / 2;
  const circumference = 2 * Math.PI * normalizedRadius;

  const c = ringColor(target);

  const dashOffset = useMemo(() => {
    const progress = animated / 1000;
    return circumference * (1 - progress);
  }, [animated, circumference]);

  useEffect(() => {
    // required for consistent UI feel: animate on mount.
    let raf = 0;
    const start = performance.now();
    const duration = 900;
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setAnimated(Math.round(eased * target));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target]);

  const dimList = [
    { key: "protection", label: "Protection" },
    { key: "discipline", label: "Discipline" },
    { key: "growth", label: "Growth" },
    { key: "family_safety", label: "Family Safety" },
    { key: "debt_health", label: "Debt Health" },
  ];

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-4 w-full max-w-[320px]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs text-gray-500 font-semibold">Arth Karma Score</div>
          <div className="text-sm text-gray-600 mt-1">{`Rank: ${percentile}`}</div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold" style={{ color: c.text, background: "#f3f4f6" }}>
          <span className={`${c.bg} text-gray-800 px-2 py-1 rounded-full`}>
            {animated}
          </span>
        </div>
      </div>

      <div className="mt-3 relative flex items-center justify-center">
        <svg height={(radius + strokeWidth) * 2} width={(radius + strokeWidth) * 2} className="block">
          <circle
            stroke="#e5e7eb"
            fill="transparent"
            strokeWidth={strokeWidth}
            r={normalizedRadius}
            cx={(radius + strokeWidth / 2) + strokeWidth / 2 - 0.5}
            cy={(radius + strokeWidth / 2) + strokeWidth / 2 - 0.5}
          />
          <circle
            stroke={c.stroke}
            fill="transparent"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference + " " + circumference}
            style={{ strokeDashoffset: dashOffset, transition: "stroke-dashoffset 0.05s linear" }}
            r={normalizedRadius}
            cx={(radius + strokeWidth / 2) + strokeWidth / 2 - 0.5}
            cy={(radius + strokeWidth / 2) + strokeWidth / 2 - 0.5}
          />
        </svg>
        <div className="absolute flex flex-col items-center justify-center">
          <div className="text-xl font-bold text-gray-900">{animated}</div>
          <div className="text-[11px] text-gray-500 font-semibold">out of 1000</div>
        </div>
      </div>

      <div className="mt-3">
        <div className="text-xs text-gray-500 font-semibold mb-2">Behavior dimensions</div>
        <div className="grid grid-cols-5 gap-2">
          {dimList.map((d) => {
            const s = Number(dims[d.key] || 0);
            return (
              <div key={d.key} className="flex flex-col items-center">
                <div className="w-full h-10 flex items-end justify-center gap-1">
                  <div
                    className="w-2 rounded-full"
                    style={{ height: `${Math.max(6, s)}%`, backgroundColor: miniColor(s) }}
                    title={`${d.label}: ${s}`}
                  />
                </div>
                <div className="text-[10px] text-gray-600">{d.label.split(" ")[0]}</div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-3 text-sm text-gray-800 font-semibold">
        {`Your ${weakest} needs attention — fix it to gain +80 points`}
      </div>
    </div>
  );
}

