import React, { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const nav = [
  { to: "/dashboard", label: "Dashboard", icon: "🏠" },
  { to: "/chat/fire", label: "FIRE Planner", icon: "🔥" },
  { to: "/chat/tax", label: "Tax Wizard", icon: "📋" },
  { to: "/chat/life_event", label: "Life Event Advisor", icon: "💡" },
  { to: "/chat/mf_xray", label: "MF Portfolio X-Ray", icon: "📊" },
  { to: "/chat/couple", label: "Couple Planner", icon: "💑" },
  { to: "/chat/mhs", label: "Money Health", icon: "❤️" },
  { to: "/mentor", label: "AI Mentor Pro", icon: "🧠" },
  { to: "/onboarding", label: "Profile onboarding", icon: "✨" },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [drawer, setDrawer] = useState(false);
  const [dark, setDark] = useState(() => localStorage.getItem("arthmitra_theme") === "dark");

  useEffect(() => {
    const root = document.documentElement;
    if (dark) {
      root.classList.add("dark");
      localStorage.setItem("arthmitra_theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("arthmitra_theme", "light");
    }
  }, [dark]);

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 md:flex">
        <div className="border-b border-slate-200 p-4 dark:border-slate-800">
          <div className="text-lg font-bold text-emerald-700 dark:text-emerald-400">ArthMitra</div>
          <div className="mt-2 truncate text-xs text-slate-500 dark:text-slate-400" title={user?.email}>
            {user?.email || "—"}
          </div>
          {user?.name ? (
            <div className="truncate text-sm font-medium text-slate-800 dark:text-slate-200">{user.name}</div>
          ) : null}
        </div>
        <nav className="flex-1 space-y-0.5 overflow-y-auto p-2">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-emerald-600 text-white shadow-sm dark:bg-emerald-600"
                    : "text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                }`
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="space-y-2 border-t border-slate-200 p-3 dark:border-slate-800">
          <button
            type="button"
            onClick={() => setDark((d) => !d)}
            className="w-full rounded-xl border border-slate-200 px-3 py-2 text-left text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            {dark ? "☀️ Light mode" : "🌙 Dark mode"}
          </button>
          <button
            type="button"
            onClick={handleLogout}
            className="w-full rounded-xl bg-red-600 px-3 py-2 text-sm font-semibold text-white hover:bg-red-700"
          >
            Log out
          </button>
        </div>
      </aside>

      {/* Mobile top bar */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-3 py-2 dark:border-slate-800 dark:bg-slate-900 md:hidden">
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="rounded-lg border border-slate-200 px-2 py-1 text-sm dark:border-slate-700"
              onClick={() => setDrawer(true)}
              aria-label="Open menu"
            >
              ☰
            </button>
            <span className="font-bold text-emerald-700 dark:text-emerald-400">ArthMitra</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="rounded-lg border border-slate-200 px-2 py-1 text-xs dark:border-slate-700"
              onClick={() => setDark((d) => !d)}
            >
              {dark ? "☀️" : "🌙"}
            </button>
            <button type="button" className="text-xs font-semibold text-red-600" onClick={handleLogout}>
              Log out
            </button>
          </div>
        </header>
        <div className="flex-1 overflow-hidden md:overflow-auto">
          <Outlet />
        </div>
      </div>

      {drawer ? (
        <div className="fixed inset-0 z-[200] md:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/50"
            aria-label="Close menu"
            onClick={() => setDrawer(false)}
          />
          <nav className="absolute left-0 top-0 flex h-full w-[min(100%,280px)] flex-col border-r border-slate-200 bg-white shadow-xl dark:border-slate-800 dark:bg-slate-900">
            <div className="border-b border-slate-200 p-4 dark:border-slate-800">
              <div className="text-sm font-bold text-emerald-700 dark:text-emerald-400">Menu</div>
              <div className="mt-1 truncate text-xs text-slate-500">{user?.email}</div>
            </div>
            <div className="flex-1 space-y-0.5 overflow-y-auto p-2">
              {nav.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setDrawer(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium ${
                      isActive
                        ? "bg-emerald-600 text-white"
                        : "text-slate-700 dark:text-slate-300"
                    }`
                  }
                >
                  <span>{item.icon}</span>
                  {item.label}
                </NavLink>
              ))}
            </div>
            <div className="border-t border-slate-200 p-3 dark:border-slate-800">
              <button
                type="button"
                className="w-full rounded-xl bg-red-600 py-2 text-sm font-semibold text-white"
                onClick={() => {
                  setDrawer(false);
                  handleLogout();
                }}
              >
                Log out
              </button>
            </div>
          </nav>
        </div>
      ) : null}
    </div>
  );
}
