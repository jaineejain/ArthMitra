import React, { useEffect, useMemo, useState } from "react";

function colorFor(score) {
  if (score < 50) return { stroke: "#dc2626", bg: "#fee2e2", text: "#b91c1c" };
  if (score < 70) return { stroke: "#d97706", bg: "#fef3c7", text: "#b45309" };
  return { stroke: "#16a34a", bg: "#dcfce7", text: "#15803d" };
}

export default function ScoreRing({ score = 0, size = "large", label = "Money Health Score" }) {
  const target = Math.max(0, Math.min(100, Number(score) || 0));
  const [animated, setAnimated] = useState(0);

  const radius = size === "large" ? 55 : 38;
  const strokeWidth = size === "large" ? 10 : 8;
  const normalizedRadius = radius - strokeWidth / 2;
  const circumference = 2 * Math.PI * normalizedRadius;

  const dashOffset = useMemo(() => {
    const progress = animated / 100;
    return circumference * (1 - progress);
  }, [animated, circumference]);

  const c = colorFor(target);

  useEffect(() => {
    // Required: animation must run on every mount.
    let raf = 0;
    const start = performance.now();
    const duration = 900;

    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      // easeOutCubic
      const eased = 1 - Math.pow(1 - t, 3);
      setAnimated(Math.round(eased * target));
      if (t < 1) raf = requestAnimationFrame(tick);
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target]);

  return (
    <div className="relative flex flex-col items-center justify-center">
      <svg height={(radius + strokeWidth / 2) * 2} width={(radius + strokeWidth / 2) * 2} className="block">
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
          style={{
            strokeDashoffset: dashOffset,
            transition: "stroke-dashoffset 0.05s linear",
          }}
          r={normalizedRadius}
          cx={(radius + strokeWidth / 2) + strokeWidth / 2 - 0.5}
          cy={(radius + strokeWidth / 2) + strokeWidth / 2 - 0.5}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <div className="text-3xl font-bold text-gray-900">{animated}</div>
        <div className="text-xs text-gray-500 font-semibold mt-1">{label}</div>
      </div>
    </div>
  );
}

