import React, { useEffect, useMemo, useState } from "react";

export default function DimensionBar({ name, score = 0, color = "#16a34a" }) {
  const target = Math.max(0, Math.min(100, Number(score) || 0));
  const [w, setW] = useState(0);

  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const duration = 650;
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setW(eased * target);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target]);

  const fillStyle = useMemo(() => ({ width: `${w}%`, backgroundColor: color }), [w, color]);

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-3">
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold text-gray-800">{name}</div>
        <div className="text-sm font-bold text-gray-900">{Math.round(target)}</div>
      </div>
      <div className="mt-2 h-3 bg-gray-100 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={fillStyle} />
      </div>
    </div>
  );
}

