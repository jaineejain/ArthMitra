import { motion } from "framer-motion";

function bandLabel(band) {
  if (band === "critical") return "Critical";
  if (band === "poor") return "Poor";
  if (band === "fair") return "Fair";
  return "Good";
}

function scoreColor(score) {
  if (score < 50) return "text-red-600 bg-red-50";
  if (score < 70) return "text-amber-700 bg-amber-50";
  return "text-green-700 bg-green-50";
}

export default function MHSCard({ data }) {
  const total = data?.total ?? 0;
  const dims = data?.dimensions || {};
  const weakest = data?.weakest;
  const band = data?.band;

  const c = scoreColor(total);

  /** Backend sends each dimension as 0–100; bar width = score/100 (NOT raw score as %) */
  const grid = [
    { key: "emergency", label: "Emergency", max: 100 },
    { key: "insurance", label: "Insurance", max: 100 },
    { key: "debt", label: "Debt", max: 100 },
    { key: "investment", label: "Investment", max: 100 },
    { key: "tax", label: "Tax", max: 100 },
    { key: "retirement", label: "Retirement", max: 100 },
  ];

  function barPct(score, max) {
    const m = max > 0 ? max : 100;
    const n = Number(score) || 0;
    return `${Math.min(100, Math.round((n / m) * 100))}%`;
  }

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.35 }}
      className="w-full bg-white rounded-2xl border border-gray-200 shadow-sm p-4 mt-3"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs text-gray-500">Money Health Score</div>
          <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ${c}`}>
            <div className="text-2xl font-bold">{total}</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-500">Band</div>
          <div className="text-lg font-semibold text-gray-900">{bandLabel(band)}</div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        {grid.map((item) => {
          const s = dims[item.key] ?? 0;
          const isWeak = item.key === weakest;
          const pct = barPct(s, item.max);
          return (
            <div
              key={item.key}
              className={`rounded-xl border p-3 ${
                isWeak ? "border-red-300 bg-red-50" : "border-gray-200 bg-gray-50"
              }`}
            >
              <div className="text-sm font-semibold text-gray-800">{item.label}</div>
              <div className="mt-2 flex items-center justify-between gap-2">
                <div className={`text-lg font-bold ${isWeak ? "text-red-700" : "text-gray-900"}`}>
                  {s}
                  <span className="text-xs font-normal text-gray-500">/{item.max}</span>
                </div>
                {isWeak ? <div className="text-xs text-red-700 font-semibold">Fix this first →</div> : null}
              </div>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-gray-200">
                <div
                  className={`h-2 rounded-full ${isWeak ? "bg-red-500" : "bg-emerald-500"}`}
                  style={{ width: pct }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}

