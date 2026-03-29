import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import ScoreRing from "../components/ScoreRing.jsx";
import DimensionBar from "../components/DimensionBar.jsx";
import KarmaScore from "../components/KarmaScore.jsx";
import { getProfile } from "../services/api.js";
import { useAuth } from "../context/AuthContext.jsx";

function formatToday() {
  return new Date().toLocaleDateString("en-IN", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function computeKarmaFallback(profile) {
  try {
    const dims = profile?.financial_profile?.mhs_dimensions || {};
    const monthlyIncome = profile?.monthly_income || 0;
    const monthlySip = profile?.financial_profile?.monthly_sip || 0;
    const termCover = profile?.financial_profile?.term_cover || 0;

    const protection = Number(dims.insurance || 0);
    const debt_health = Number(dims.debt || 0);
    const discipline = monthlySip > 0 ? 100 : 0;
    const growth = monthlyIncome > 0 ? Math.min(100, (monthlySip / monthlyIncome) * 500) : 0;
    const termNeeded = Math.max(1, monthlyIncome) * 12 * 15;
    const family_safety = termNeeded > 0 ? Math.min(100, (termCover / termNeeded) * 100) : 0;

    const total100 =
      protection * 0.2 +
      discipline * 0.25 +
      growth * 0.2 +
      family_safety * 0.2 +
      debt_health * 0.15;
    const total = Math.round(total100 * 10);

    let percentile = "Top 30%";
    if (total >= 900) percentile = "Top 1%";
    else if (total >= 800) percentile = "Top 5%";
    else if (total >= 700) percentile = "Top 10%";
    else if (total >= 600) percentile = "Top 20%";

    const weakestKey = Object.entries(dims).sort((a, b) => Number(a[1]) - Number(b[1]))[0]?.[0] || "investment";
    return {
      total,
      dimensions: {
        protection: protection,
        discipline: discipline,
        growth: Math.round(growth),
        family_safety: Math.round(family_safety),
        debt_health: debt_health,
      },
      weakest: weakestKey,
      percentile,
    };
  } catch {
    return { total: 0, dimensions: {}, weakest: "investment", percentile: "Top 30%" };
  }
}

export default function Dashboard() {
  const { userId, user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      const res = await getProfile(userId);
      if (mounted) {
        setProfile(res.data || null);
        setLoading(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, [userId]);

  const mhsScore = profile?.financial_profile?.mhs_score ?? 0;
  const dims = profile?.financial_profile?.mhs_dimensions || {};

  const karma = profile?.karma_score || computeKarmaFallback(profile);

  const dimensionItems = useMemo(
    () => [
      { name: "Emergency", score: dims.emergency || 0, color: "#16a34a" },
      { name: "Insurance", score: dims.insurance || 0, color: "#d97706" },
      { name: "Debt", score: dims.debt || 0, color: "#2563eb" },
      { name: "Investment", score: dims.investment || 0, color: "#16a34a" },
      { name: "Tax", score: dims.tax || 0, color: "#d97706" },
      { name: "Retirement", score: dims.retirement || 0, color: "#2563eb" },
    ],
    [dims]
  );

  const name = profile?.name || "friend";

  const featureCards = [
    { icon: "🔥", title: "FIRE Planner", desc: "Build your financial freedom path", to: "/chat/fire" },
    { icon: "📋", title: "Tax Wizard", desc: "Save maximum tax this year", to: "/chat/tax" },
    { icon: "💡", title: "Life Event Advisor", desc: "Plan big moments with calm clarity", to: "/chat/life_event" },
    { icon: "📊", title: "MF Portfolio X-Ray", desc: "Detect overlap, cost & improve returns", to: "/chat/mf_xray" },
    { icon: "💑", title: "Couple's Planner", desc: "Optimize jointly for slab efficiency", to: "/chat/couple" },
    { icon: "❤️", title: "Money Health Details", desc: "Spot weakest areas first", to: "/chat/mhs" },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-[#fafaf8] p-4 dark:bg-slate-950 md:p-8">
        <div className="mx-auto max-w-5xl space-y-6">
          <div className="h-10 w-64 animate-pulse rounded-xl bg-gray-200 dark:bg-slate-800" />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-12">
            <div className="mx-auto h-48 w-48 animate-pulse rounded-full bg-gray-200 dark:bg-slate-800 md:col-span-4" />
            <div className="space-y-3 md:col-span-8">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-12 animate-pulse rounded-xl bg-gray-200 dark:bg-slate-800" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#fafaf8] p-4 dark:bg-slate-950 md:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">Namaste, {name}! 👋</div>
          <div className="mt-1 text-sm text-gray-600 dark:text-slate-400">{formatToday()}</div>
          {user?.email ? (
            <div className="mt-1 text-xs text-gray-500 dark:text-slate-500">{user.email}</div>
          ) : null}
        </div>
        <Link
          to="/mentor"
          className="rounded-2xl bg-gradient-to-r from-cyan-600 to-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-md hover:opacity-95"
        >
          Open AI Money Mentor Pro →
        </Link>
      </div>

      <div className="mt-6 grid grid-cols-1 items-start gap-6 md:grid-cols-12">
        <div className="flex justify-center md:col-span-4 md:justify-start">
          <ScoreRing score={mhsScore} size="large" label="Money Health Score" />
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:col-span-8">
          {dimensionItems.map((d) => (
            <DimensionBar key={d.name} name={d.name} score={d.score} color={d.color} />
          ))}
        </div>
      </div>

      <div className="mt-8">
        <div className="text-lg font-semibold text-gray-900 dark:text-white">What would you like to work on?</div>
        <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {featureCards.map((c) => (
            <Link
              key={c.to}
              to={c.to}
              className="flex items-center justify-between gap-3 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm transition-shadow duration-200 hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
            >
              <div>
                <div className="text-2xl">{c.icon}</div>
                <div className="mt-1 font-semibold text-gray-900 dark:text-white">{c.title}</div>
                <div className="mt-1 text-sm text-gray-600 dark:text-slate-400">{c.desc}</div>
              </div>
              <div className="text-xl font-bold text-gray-400">→</div>
            </Link>
          ))}
        </div>
      </div>

      <div className="fixed bottom-5 right-5 hidden md:block">
        <KarmaScore data={karma} />
      </div>
    </div>
  );
}

