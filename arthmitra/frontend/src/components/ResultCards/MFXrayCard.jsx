import { motion } from "framer-motion";

function formatINR(paise) {
  const rupees = (paise || 0) / 100;
  return `₹${new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(rupees)}`;
}

function formatPct(x) {
  return `${(Number(x) * 100).toFixed(1)}%`;
}

function xirrColor(x) {
  if (x < 0) return "text-red-700 bg-red-50";
  if (x < 0.1) return "text-amber-700 bg-amber-50";
  return "text-green-700 bg-green-50";
}

export default function MFXrayCard({ data }) {
  const portfolio = data?.portfolio || [];

  const totalInvested = data?.total_invested || 0;
  const totalCurrent = data?.total_current || 0;

  const overlapWarnings = [];
  const anyRegular = portfolio.some((f) => f.plan === "regular");
  portfolio.forEach((f) => {
    (f.overlaps || []).forEach((o) => {
      if ((o.pct || 0) >= 60) {
        overlapWarnings.push({
          pair: `${f.fund_name} ↔ ${o.fund_name}`,
          pct: o.pct,
        });
      }
    });
  });

  const avgXirr = portfolio.length
    ? portfolio.reduce((acc, f) => acc + (f.xirr || 0), 0) / portfolio.length
    : 0;

  const expenseFlags = portfolio.filter((f) => (f.expense_ratio || 0) > 1);
  const rebalancePlan = [];
  if (expenseFlags.length) {
    rebalancePlan.push(
      ...expenseFlags.slice(0, 2).map((f) => ({
        title: `Reduce cost: ${f.fund_name}`,
        reason: `Expense ratio is ${f.expense_ratio.toFixed(2)}% (>1%). Prefer a direct/good-cost alternative.`,
      }))
    );
  }
  if (overlapWarnings.length) {
    rebalancePlan.push({
      title: "Cut redundant overlap",
      reason: `Overlap is high for: ${overlapWarnings[0].pair}. Avoid stacking near-identical exposures.`,
    });
  }
  if (anyRegular) {
    rebalancePlan.push({
      title: "Prefer direct plans where possible",
      reason: "Regular plans carry higher ongoing costs; direct plan typically improves net returns.",
    });
  }
  if (!rebalancePlan.length) {
    rebalancePlan.push({
      title: "Keep the allocation steady",
      reason: "No major red flags detected. Rebalance only if market/holdings drift materially.",
    });
  }

  const planActions = rebalancePlan.slice(0, 5);

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.35 }}
      className="w-full bg-white rounded-2xl border border-gray-200 shadow-sm p-4 mt-3"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs text-gray-500">Portfolio summary</div>
          <div className="text-lg font-semibold text-gray-900">
            {formatINR(totalInvested)} invested → {formatINR(totalCurrent)} current
          </div>
          <div className="text-sm text-gray-600 mt-1">
            Overall avg XIRR:{" "}
            <span
              className={`${xirrColor(avgXirr)} inline-flex items-center px-2 py-1 rounded-full font-semibold`}
            >
              {formatPct(avgXirr)}
            </span>
          </div>
        </div>
        {overlapWarnings.length ? (
          <div className="bg-red-50 text-red-800 px-3 py-1 rounded-full text-sm font-semibold">
            ⚠️ High overlap detected
          </div>
        ) : (
          <div className="bg-green-50 text-green-800 px-3 py-1 rounded-full text-sm font-semibold">
            ✅ Overlap looks ok
          </div>
        )}
      </div>

      <div className="mt-4 text-sm font-semibold text-gray-800">Funds</div>
      <div className="mt-2 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-500">
              <th className="py-2">Fund</th>
              <th className="py-2">Plan</th>
              <th className="py-2">XIRR</th>
              <th className="py-2">Expense</th>
              <th className="py-2">Overlap</th>
            </tr>
          </thead>
          <tbody>
            {portfolio.map((f, idx) => (
              <tr key={idx} className="border-t border-gray-100">
                <td className="py-2 font-medium text-gray-800">{f.fund_name}</td>
                <td className="py-2">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-semibold ${
                      f.plan === "direct" ? "bg-green-50 text-green-700" : "bg-amber-50 text-amber-800"
                    }`}
                  >
                    {f.plan}
                  </span>
                </td>
                <td className="py-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-semibold ${xirrColor(f.xirr || 0)}`}>
                    {formatPct(f.xirr || 0)}
                  </span>
                </td>
                <td className="py-2 text-gray-700">{(f.expense_ratio || 0).toFixed(2)}%</td>
                <td className="py-2">
                  {(f.overlaps || []).length ? (
                    <span className="text-xs font-semibold text-red-700 bg-red-50 px-2 py-1 rounded-full">
                      {f.overlaps[0].pct}%+
                    </span>
                  ) : (
                    <span className="text-xs text-gray-500">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {overlapWarnings.length ? (
        <div className="mt-4">
          <div className="text-sm font-semibold text-red-800">Overlap warnings</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {overlapWarnings.slice(0, 3).map((w, idx) => (
              <div key={idx} className="bg-red-50 text-red-800 px-3 py-1 rounded-full text-xs font-semibold">
                {w.pair}: {w.pct}%
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="mt-4 text-sm font-semibold text-gray-800">Rebalancing plan</div>
      <div className="mt-2 space-y-2">
        {planActions.map((a, idx) => (
          <div key={idx} className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-gray-100 text-gray-800 flex items-center justify-center text-sm font-bold">
              {idx + 1}
            </div>
            <div>
              <div className="text-sm font-semibold text-gray-900">{a.title}</div>
              <div className="text-sm text-gray-600">{a.reason}</div>
            </div>
          </div>
        ))}
      </div>

      {anyRegular ? (
        <div className="mt-4 bg-amber-50 text-amber-800 rounded-xl p-3 text-sm font-semibold">
          Regular plan funds found — consider switching to direct to reduce ongoing cost.
        </div>
      ) : null}
    </motion.div>
  );
}

