import React, { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../context/AuthContext.jsx";
import { forgotPasswordRequest, resetPasswordRequest } from "../services/api.js";

export default function Login() {
  const { login, isAuthenticated, bootstrapping } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const [forgotOpen, setForgotOpen] = useState(false);
  const [forgotStep, setForgotStep] = useState("request"); // request | reset
  const [forgotEmail, setForgotEmail] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotError, setForgotError] = useState("");

  if (!bootstrapping && isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  function validate() {
    const e = {};
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = "Enter a valid email";
    if (!password) e.password = "Password is required";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSubmit(ev) {
    ev.preventDefault();
    if (!validate()) return;
    setLoading(true);
    const res = await login(email.trim(), password);
    setLoading(false);
    if (res.error) {
      toast.error(String(res.error), { id: "login-error", duration: 4500 });
      return;
    }
    toast.success("Welcome back!");
    navigate("/dashboard", { replace: true });
  }

  async function handleForgotRequest(ev) {
    ev.preventDefault();
    setForgotError("");
    const e = forgotEmail.trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e)) {
      setForgotError("Enter a valid email address");
      return;
    }
    setForgotLoading(true);
    try {
      const res = await forgotPasswordRequest(e);
      if (res.error) {
        toast.error(String(res.error), { id: "forgot-error", duration: 4500 });
        return;
      }
      setResetToken(res.data.reset_token);
      setForgotStep("reset");
    } finally {
      setForgotLoading(false);
    }
  }

  async function handleResetPassword(ev) {
    ev.preventDefault();
    setForgotError("");
    if (!newPassword || newPassword.length < 8) {
      setForgotError("Password must be at least 8 characters");
      return;
    }
    if (newPassword !== confirmPassword) {
      setForgotError("Passwords do not match");
      return;
    }
    setForgotLoading(true);
    try {
      const res = await resetPasswordRequest(resetToken, newPassword);
      if (res.error) {
        toast.error(String(res.error), { id: "reset-error", duration: 4500 });
        return;
      }
      toast.success("Password reset successful. Please log in with your new password.");
      setForgotOpen(false);
      setForgotStep("request");
      setForgotEmail("");
      setResetToken("");
      setNewPassword("");
      setConfirmPassword("");
    } finally {
      setForgotLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-emerald-50 p-4 dark:from-slate-950 dark:to-slate-900">
      <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-xl dark:border-slate-800 dark:bg-slate-900">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Log in</h1>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">ArthMitra — your AI money mentor</p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Email</label>
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-900 outline-none focus:border-emerald-500 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
              placeholder="you@example.com"
              disabled={loading}
            />
            {errors.email ? <p className="mt-1 text-xs text-red-600">{errors.email}</p> : null}
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Password</label>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-900 outline-none focus:border-emerald-500 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
              placeholder="••••••••"
              disabled={loading}
            />
            {errors.password ? <p className="mt-1 text-xs text-red-600">{errors.password}</p> : null}
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-emerald-600 py-3 text-sm font-bold text-white shadow-lg hover:bg-emerald-700 disabled:opacity-60"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            type="button"
            className="text-sm font-semibold text-slate-600 hover:underline dark:text-slate-300"
            onClick={() => {
              setForgotOpen(true);
              setForgotStep("request");
              setForgotError("");
            }}
            disabled={loading}
          >
            Forgot password?
          </button>
        </div>

        {forgotOpen ? (
          <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/60">
            <div className="mb-2 text-sm font-bold text-slate-900 dark:text-white">
              {forgotStep === "request" ? "Reset password" : "Set new password"}
            </div>

            {forgotError ? (
              <div className="mb-3 rounded-xl border border-red-200 bg-red-50 p-2 text-xs text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-200">
                {forgotError}
              </div>
            ) : null}

            {forgotStep === "request" ? (
              <form onSubmit={handleForgotRequest} className="space-y-3">
                <input
                  type="email"
                  value={forgotEmail}
                  onChange={(e) => setForgotEmail(e.target.value)}
                  placeholder="you@example.com"
                  disabled={forgotLoading}
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-emerald-500 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                />
                <button
                  type="submit"
                  disabled={forgotLoading}
                  className="w-full rounded-xl bg-emerald-600 py-3 text-sm font-bold text-white shadow-lg hover:bg-emerald-700 disabled:opacity-60"
                >
                  {forgotLoading ? "Sending token…" : "Get reset token"}
                </button>
              </form>
            ) : (
              <form onSubmit={handleResetPassword} className="space-y-3">
                <div className="text-xs text-slate-600 dark:text-slate-300">
                  Your reset token (demo): paste it below. Token expires in 15 minutes.
                </div>
                <input
                  type="text"
                  value={resetToken}
                  readOnly
                  disabled={forgotLoading}
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-xs text-slate-900 outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                />
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="New password"
                  disabled={forgotLoading}
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-emerald-500 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm password"
                  disabled={forgotLoading}
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-emerald-500 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                />
                <button
                  type="submit"
                  disabled={forgotLoading}
                  className="w-full rounded-xl bg-emerald-600 py-3 text-sm font-bold text-white shadow-lg hover:bg-emerald-700 disabled:opacity-60"
                >
                  {forgotLoading ? "Resetting…" : "Reset password"}
                </button>
                <button
                  type="button"
                  disabled={forgotLoading}
                  onClick={() => {
                    setForgotStep("request");
                    setResetToken("");
                    setNewPassword("");
                    setConfirmPassword("");
                    setForgotError("");
                  }}
                  className="w-full text-sm font-semibold text-slate-600 hover:underline dark:text-slate-300"
                >
                  Back
                </button>
              </form>
            )}
          </div>
        ) : null}

        <p className="mt-6 text-center text-sm text-slate-600 dark:text-slate-400">
          No account?{" "}
          <Link to="/signup" className="font-semibold text-emerald-600 hover:underline dark:text-emerald-400">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
