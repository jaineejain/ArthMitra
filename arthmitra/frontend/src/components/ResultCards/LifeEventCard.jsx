import { motion } from "framer-motion";

export default function LifeEventCard({ data }) {
  const eventType = data?.event_type || "Life Event";
  const allocations = data?.allocations || [];
  const timeline = data?.timeline_days ?? null;
  const totalSaving = data?.tax_saving ?? null;

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.35 }}
      className="w-full bg-white rounded-2xl border border-gray-200 shadow-sm p-4 mt-3"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs text-gray-500">Event advisor</div>
          <div className="text-xl font-bold text-gray-900">{eventType}</div>
        </div>
        {typeof totalSaving === "number" ? (
          <div className="bg-green-50 text-green-700 px-3 py-1 rounded-full text-sm font-semibold">
            Save around ₹{(totalSaving / 100).toLocaleString("en-IN")}
          </div>
        ) : null}
      </div>

      {Array.isArray(allocations) && allocations.length > 0 ? (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500">
                <th className="py-2">Priority</th>
                <th className="py-2">Action</th>
                <th className="py-2">Amount</th>
                <th className="py-2">Reason</th>
              </tr>
            </thead>
            <tbody>
              {allocations.map((row, idx) => (
                <tr key={idx} className="border-t border-gray-100">
                  <td className="py-2 font-medium text-gray-700">{row.priority || idx + 1}</td>
                  <td className="py-2 text-gray-800">{row.action || row.title || "-"}</td>
                  <td className="py-2 font-semibold text-gray-900">
                    ₹{Math.round((row.amount || 0) / 100).toLocaleString("en-IN")}
                  </td>
                  <td className="py-2 text-gray-600">{row.reason || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="mt-4 text-sm text-gray-500">No allocation table yet.</div>
      )}

      {timeline !== null ? (
        <div className="mt-4 bg-blue-50 text-blue-800 rounded-xl p-3 text-sm font-semibold">
          Do this within {timeline} days
        </div>
      ) : null}
    </motion.div>
  );
}

