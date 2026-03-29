import React, { useEffect, useRef, useState } from "react";
import { fetchWatchdogAlerts } from "../../services/api.js";

export default function NotificationBell({ onPickAlert }) {
  const [open, setOpen] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const ref = useRef(null);

  useEffect(() => {
    function close(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("click", close);
    return () => document.removeEventListener("click", close);
  }, []);

  async function load() {
    const r = await fetchWatchdogAlerts();
    if (r.data?.alerts) setAlerts(r.data.alerts);
  }

  useEffect(() => {
    load();
  }, []);

  const unread = alerts.length;

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => {
          setOpen(!open);
          load();
        }}
        className="relative rounded-xl border border-slate-600 p-2 text-slate-300 hover:bg-slate-800"
        aria-label="Alerts"
      >
        <span className="text-lg">🔔</span>
        {unread > 0 ? (
          <span className="absolute -right-1 -top-1 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-[#ff6b6b] px-1 text-[10px] font-bold text-white">
            {unread}
          </span>
        ) : null}
      </button>
      {open ? (
        <div className="absolute right-0 z-50 mt-2 w-80 max-h-96 overflow-y-auto rounded-2xl border border-slate-700 bg-slate-900 p-2 shadow-2xl">
          <div className="mb-2 text-xs font-bold uppercase text-slate-500">Watchdog (demo)</div>
          {alerts.map((a) => (
            <button
              key={a.id}
              type="button"
              onClick={() => {
                onPickAlert?.(a.action_prompt || a.title);
                setOpen(false);
              }}
              className="mb-2 w-full rounded-xl border border-slate-700 bg-slate-950/80 p-3 text-left text-sm hover:border-cyan-500/40"
            >
              <div className="font-semibold text-slate-100">{a.title}</div>
              <div className="mt-1 text-xs text-slate-400">{a.description}</div>
              <div className="mt-2 text-xs font-semibold text-cyan-400">Fix this →</div>
            </button>
          ))}
          {alerts.length === 0 ? <div className="p-2 text-xs text-slate-500">No alerts</div> : null}
        </div>
      ) : null}
    </div>
  );
}
