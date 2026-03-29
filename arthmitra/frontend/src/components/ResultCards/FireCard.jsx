import { motion } from "framer-motion";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function formatINRFromPaise(paise, { withDecimals = false } = {}) {
  const rupees = (paise || 0) / 100;
  const formatter = new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: withDecimals ? 2 : 0,
    minimumFractionDigits: withDecimals ? 2 : 0,
  });
  return `₹${formatter.format(rupees)}`;
}

function formatCroresFromPaise(paise) {
  const crores = (paise || 0) / (100 * 10_000_000);
  return `₹${crores.toFixed(2)} Crore`;
}

export default function FireCard({ data }) {
  const achievable = Boolean(data?.achievable);
  const sipGap = data?.sip_gap || 0;
  const monthlyGapRu = Math.round(sipGap / 100);

  const chartData = (data?.chart_data || []).map((d) => ({
    t: d.t,
    current: (d.current || 0) / (100 * 10_000_000), // crores
    required: (d.required || 0) / (100 * 10_000_000), // crores
  }));

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.35 }}
      className="w-full bg-white rounded-2xl border border-gray-200 shadow-sm p-4 mt-3"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm text-gray-500">Corpus needed</div>
          <div className="text-3xl font-bold text-green-700">{formatCroresFromPaise(data?.fire_corpus)}</div>
        </div>
        <div
          className={`px-3 py-1 rounded-full text-sm font-semibold ${
            achievable ? "bg-green-50 text-green-700" : "bg-amber-50 text-amber-700"
          }`}
        >
          {achievable ? "✅ Achievable" : `⚠️ Increase SIP by ${formatINRFromPaise(sipGap)}`}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mt-4">
        <div className="bg-gray-50 rounded-xl p-3">
          <div className="text-xs text-gray-500">Monthly SIP Needed</div>
          <div className="text-lg font-semibold">{formatINRFromPaise(data?.sip_needed, { withDecimals: false })}</div>
        </div>
        <div className="bg-gray-50 rounded-xl p-3">
          <div className="text-xs text-gray-500">Your Current SIP</div>
          <div className="text-lg font-semibold">{formatINRFromPaise(data?.current_sip, { withDecimals: false })}</div>
        </div>
        <div className="bg-gray-50 rounded-xl p-3">
          <div className="text-xs text-gray-500">Monthly Gap</div>
          <div className={`text-lg font-semibold ${monthlyGapRu > 0 ? "text-red-600" : "text-gray-900"}`}>
            {formatINRFromPaise(sipGap, { withDecimals: false })}
          </div>
        </div>
        <div className="bg-gray-50 rounded-xl p-3">
          <div className="text-xs text-gray-500">Years to FIRE</div>
          <div className="text-lg font-semibold">{data?.years ?? 0} years</div>
        </div>
      </div>

      <div className="mt-4">
        <div className="text-sm font-semibold text-gray-800 mb-2">Trajectory (5 snapshots)</div>
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="t" tick={{ fontSize: 12 }} />
              <YAxis
                tick={{ fontSize: 12 }}
                tickFormatter={(v) => `${v.toFixed(2)} cr`}
              />
              <Tooltip
                formatter={(v) => `${v.toFixed(2)} cr`}
                labelFormatter={(label) => `Year ~ ${label}`}
              />
              <Area
                type="monotone"
                dataKey="current"
                name="Current Trajectory"
                stroke="#f59e0b"
                fill="#fef3c7"
                strokeWidth={2}
                strokeDasharray="6 6"
              />
              <Area
                type="monotone"
                dataKey="required"
                name="Required Trajectory"
                stroke="#16a34a"
                fill="#dcfce7"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="text-xs text-gray-500 mt-3">
        Tip: Use this as a planning compass; fine-tune later with exact assumptions.
      </div>
    </motion.div>
  );
}

