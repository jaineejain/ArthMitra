import { motion } from "framer-motion";

function formatINR(paise, { withDecimals = false } = {}) {
  const rupees = (paise || 0) / 100;
  const formatter = new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: withDecimals ? 2 : 0,
    minimumFractionDigits: withDecimals ? 2 : 0,
  });
  return `₹${formatter.format(rupees)}`;
}

function formatPct(n) {
  return `${Math.round((n || 0) * 100)}%`;
}

export default function TaxCard({ data }) {
  const oldTax = data?.old_tax || 0;
  const newTax = data?.new_tax || 0;
  const recommended = data?.recommended || "new";
  const savings = data?.savings || 0;
  const winner = recommended === "old" ? "Old Regime" : "New Regime";

  const missed = Array.isArray(data?.missed_deductions) ? data.missed_deductions : [];

  // 80C utilization: use used_80c if backend provides, else approximate by min(old_taxable gap).
  const used80c = data?.used_80c ?? null;
  const utilization = used80c === null ? null : Math.min(1, (used80c || 0) / (150000 * 100));

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.35 }}
      className="w-full bg-white rounded-2xl border border-gray-200 shadow-sm p-4 mt-3"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs text-gray-500">Tax optimization winner</div>
          <div className="text-xl font-bold text-gray-900">{winner}</div>
        </div>
        <div className="bg-amber-50 text-amber-800 px-3 py-1 rounded-full text-sm font-semibold">
          {recommended === "old"
            ? `Old Regime saves you ${formatINR(savings)}`
            : `New Regime saves you ${formatINR(savings)}`}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mt-4">
        <div className="bg-gray-50 rounded-xl p-3">
          <div className="text-sm font-semibold text-gray-800">Old Regime</div>
          <div className="text-xs text-gray-500 mt-1">Taxable income</div>
          <div className="text-lg font-semibold">{formatINR(data?.old_taxable || 0)}</div>
          <div className="text-xs text-gray-500 mt-3">Total tax</div>
          <div className="text-lg font-bold text-gray-900">{formatINR(oldTax)}</div>
        </div>
        <div className="bg-gray-50 rounded-xl p-3">
          <div className="text-sm font-semibold text-gray-800">New Regime</div>
          <div className="text-xs text-gray-500 mt-1">Taxable income</div>
          <div className="text-lg font-semibold">{formatINR(data?.new_taxable || 0)}</div>
          <div className="text-xs text-gray-500 mt-3">Total tax</div>
          <div className="text-lg font-bold text-gray-900">{formatINR(newTax)}</div>
        </div>
      </div>

      <div className="mt-4">
        <div className="text-sm font-semibold text-gray-800 mb-2">Missed deductions</div>
        <div className="space-y-2">
          {missed.slice(0, 5).map((item, idx) => (
            <div key={idx} className="flex items-center justify-between bg-gray-50 rounded-xl p-3">
              <div className="text-sm text-gray-800 font-medium">{item?.name}</div>
              <div className="text-sm font-semibold text-green-700">
                Potential: {formatINR(item?.potential || 0)}
                {item?.saving ? <span className="text-gray-500"> · Save {formatINR(item.saving)}</span> : null}
              </div>
            </div>
          ))}
          {missed.length === 0 ? <div className="text-sm text-gray-500">No missed deductions found.</div> : null}
        </div>
      </div>

      <div className="mt-4">
        <div className="text-sm font-semibold text-gray-800 mb-2">80C utilization</div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-2 bg-green-500"
            style={{ width: `${Math.round((utilization ?? 0) * 100)}%` }}
          />
        </div>
        <div className="text-xs text-gray-500 mt-2">
          {utilization === null
            ? "Provide 80C used to show exact utilization."
            : `Used ${formatINR(used80c)} of ${formatINR(150000 * 100)}.`}
        </div>
      </div>

      <div className="mt-4 bg-blue-50 text-blue-800 rounded-xl p-3 text-sm font-semibold">
        Optimize before March 31
      </div>
    </motion.div>
  );
}

