import axios from "axios";

const TOKEN_KEY = "arthmitra_token";
const USER_KEY = "arthmitra_user";

/**
 * Dev: empty baseURL → requests hit Vite (5173), proxy forwards to FastAPI.
 * Prod: set VITE_API_URL to your API origin (e.g. https://api.example.com).
 * Direct: VITE_API_URL=http://127.0.0.1:8000 if you skip the proxy.
 */
function resolveApiBaseURL() {
  const fromEnv = (import.meta.env.VITE_API_URL ?? "").trim();
  if (fromEnv) return fromEnv;
  if (import.meta.env.DEV) return "";
  return "http://127.0.0.1:8000";
}

const api = axios.create({
  baseURL: resolveApiBaseURL(),
  timeout: 60000,
});

/** User-friendly message when backend is down or URL is wrong */
export function formatAxiosError(error) {
  if (!error?.response) {
    const code = error?.code || "";
    const msg = error?.message || "";
    if (msg === "Network Error" || code === "ERR_NETWORK" || code === "ECONNREFUSED" || code === "ERR_CONNECTION_REFUSED") {
      return "Cannot reach the API. Start the backend: uvicorn on 127.0.0.1:8000, then run npm run dev (Vite proxies /auth and /api).";
    }
    return msg || "Network error";
  }
  const d = error.response.data;
  if (typeof d?.detail === "string") return d.detail;
  if (Array.isArray(d?.detail)) {
    return d.detail.map((x) => (typeof x === "object" ? x.msg || JSON.stringify(x) : String(x))).join("; ");
  }
  if (d && typeof d === "object" && d.message) return String(d.message);
  return error.response.statusText || "Request failed";
}

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setAuthSession(token, user) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    if (user.user_id || user.id) {
      localStorage.setItem("user_id", user.user_id || user.id);
    }
  } else {
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem("user_id");
  }
}

export function clearAuthSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem("user_id");
}

api.interceptors.request.use((config) => {
  const t = getStoredToken();
  if (t) {
    config.headers.Authorization = `Bearer ${t}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      const path = window.location.pathname || "";
      if (!path.startsWith("/login") && !path.startsWith("/signup")) {
        clearAuthSession();
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

export async function signupRequest(name, email, password) {
  try {
    const res = await api.post("/auth/signup", { name, email, password });
    return { data: res.data, error: null };
  } catch (e) {
    return { data: null, error: formatAxiosError(e) };
  }
}

export async function loginRequest(email, password) {
  try {
    const res = await api.post("/auth/login", { email, password });
    return { data: res.data, error: null };
  } catch (e) {
    return { data: null, error: formatAxiosError(e) };
  }
}

export async function forgotPasswordRequest(email) {
  try {
    const res = await api.post("/auth/forgot-password", { email });
    return { data: res.data, error: null };
  } catch (e) {
    return { data: null, error: formatAxiosError(e) };
  }
}

export async function resetPasswordRequest(resetToken, newPassword) {
  try {
    const res = await api.post("/auth/reset-password", {
      reset_token: resetToken,
      new_password: newPassword,
    });
    return { data: res.data, error: null };
  } catch (e) {
    return { data: null, error: formatAxiosError(e) };
  }
}

export async function fetchAuthMe() {
  try {
    const res = await api.get("/auth/me");
    return { data: res.data, error: null };
  } catch (e) {
    return { data: null, error: formatAxiosError(e) };
  }
}

/** @deprecated Anonymous signup disabled — use signupRequest */
export async function createUser() {
  return { data: null, error: "Please sign up with email and password." };
}

export async function sendMessage(message, feature, history) {
  try {
    const res = await api.post("/api/chat", {
      message,
      feature,
      history: history || [],
    });
    return { data: res.data, error: null };
  } catch (e) {
    return { data: null, error: e?.response?.data || e.message || String(e) };
  }
}

export async function fetchChatHistory(feature) {
  try {
    const res = await api.get(`/api/chat/history/${feature}`);
    return { data: res.data, error: null };
  } catch (e) {
    return { data: null, error: e?.response?.data || e.message || String(e) };
  }
}

export async function clearModuleChat(feature) {
  try {
    const res = await api.delete(`/api/chat/history/${feature}`);
    return { data: res.data, error: null };
  } catch (e) {
    return { data: null, error: e?.response?.data || e.message || String(e) };
  }
}

export async function completeOnboarding(conversation) {
  try {
    const res = await api.post("/api/chat/onboarding-complete", {
      conversation: conversation || [],
    });
    return { data: res.data, error: null };
  } catch (e) {
    return { data: null, error: e?.response?.data || e.message || String(e) };
  }
}

export async function getProfile(userId) {
  try {
    const res = await api.get(`/api/users/${userId}`);
    return { data: res.data, error: null };
  } catch (e) {
    return { data: null, error: e?.response?.data || e.message || String(e) };
  }
}

export async function uploadFile(file, type) {
  try {
    const endpoint = type === "form16" ? "/api/upload/form16" : "/api/upload/cams";
    if (file) {
      const formData = new FormData();
      formData.append("file", file);
      const res = await api.post(endpoint, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return { data: res.data, error: null };
    }
    const res = await api.post(endpoint);
    return { data: res.data, error: null };
  } catch (e) {
    return { data: null, error: e?.response?.data || e.message || String(e) };
  }
}

export async function mentorChat(message, history, options = {}) {
  const lang = options.language || "hinglish";
  const professional_ca =
    options.professional_ca !== undefined
      ? Boolean(options.professional_ca)
      : String(lang).toLowerCase() === "english";
  try {
    const res = await api.post("/api/v2/mentor/chat", {
      message,
      history: history || [],
      language: lang,
      expert_mode: Boolean(options.expert_mode),
      auto_detect_language: options.auto_detect_language !== false,
      display_name: options.display_name || null,
      professional_ca,
      planner_section: options.planner_section || null,
    });
    return { data: res.data, error: null };
  } catch (e) {
    return { data: null, error: e?.response?.data || e.message || String(e) };
  }
}

export async function fetchWatchdogAlerts() {
  try {
    const res = await api.get("/api/v2/mentor/watchdog/alerts");
    return { data: res.data, error: null };
  } catch (e) {
    return { data: null, error: e?.response?.data || e.message || String(e) };
  }
}

export async function mentorHealth() {
  try {
    const res = await api.get("/api/v2/mentor/health");
    return { data: res.data, error: null };
  } catch (e) {
    return { data: null, error: e?.response?.data || e.message || String(e) };
  }
}

export async function simulateWealth(body) {
  try {
    const res = await api.post("/api/v2/mentor/simulate/wealth", body);
    return { data: res.data, error: null };
  } catch (e) {
    return { data: null, error: e?.response?.data || e.message || String(e) };
  }
}

export { api };
