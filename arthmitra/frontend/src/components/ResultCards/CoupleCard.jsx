import { motion } from "framer-motion";

function formatINR(paise) {
  const rupees = (paise || 0) / 100;
  return `₹${new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(rupees)}`;
}

export default function CoupleCard({ data }) {
  const oldTax = data?.combined_old_tax || 0;
  const optTax = data?.combined_optimized_tax || 0;
  const saving = data?.annual_saving || 0;
  const sipP1 = data?.sip_split_p1_pct ?? 0;
  const sipP2 = data?.sip_split_p2_pct ?? 0;

  const hraAdvice = data?.hra_advice || "Optimize HRA claim for slab efficiency.";

  const tips = [
    `HRA: ${hraAdvice}`,
    `SIP/80C split idea: lower-income partner gets more (Partner A ${sipP1}% / Partner B ${sipP2}%).`,
    "NPS: keep both partners eligible under 80CCD(1B)/80CCD(1) limits if applicable.",
  ];

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.35 }}
      className="w-full bg-white rounded-2xl border border-gray-200 shadow-sm p-4 mt-3"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs text-gray-500">Couple optimization</div>
          <div className="text-lg font-semibold text-gray-900">
            You save <span className="text-green-700">{formatINR(saving)}/year</span> together
          </div>
        </div>
        <div className="bg-green-50 text-green-800 px-3 py-1 rounded-full text-sm font-semibold">
          ✅ Joint tax better
        </div>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-3 items-center">
        <div className="col-span-1 bg-blue-50 rounded-xl p-3">
          <div className="text-sm font-semibold text-blue-900">Baseline</div>
          <div className="mt-2 text-xs text-blue-800 font-medium">Combined tax</div>
          <div className="mt-1 text-lg font-bold text-blue-900">{formatINR(oldTax)}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 font-semibold">Optimized</div>
          <div className="mt-2 text-2xl">→</div>
        </div>
        <div className="col-span-1 bg-pink-50 rounded-xl p-3">
          <div className="text-sm font-semibold text-pink-900">After optimization</div>
          <div className="mt-2 text-xs text-pink-800 font-medium">Combined tax</div>
          <div className="mt-1 text-lg font-bold text-pink-900">{formatINR(optTax)}</div>
        </div>
      </div>

      <div className="mt-4">
        <div className="text-sm font-semibold text-gray-800">Optimization tips</div>
        <div className="mt-2 space-y-2">
          {tips.map((t, idx) => (
            <div key={idx} className="flex gap-3 items-start">
              <div className="w-7 h-7 rounded-full bg-gray-100 text-gray-800 flex items-center justify-center text-xs font-bold">
                {idx + 1}
              </div>
              <div className="text-sm text-gray-700">{t}</div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

