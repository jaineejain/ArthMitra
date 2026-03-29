import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/** Forward API calls to FastAPI — avoids CORS + Windows localhost/IPv6 issues */
const API_TARGET = process.env.VITE_PROXY_TARGET || "http://127.0.0.1:8000";

const proxy = {
  "/auth": { target: API_TARGET, changeOrigin: true },
  "/api": { target: API_TARGET, changeOrigin: true },
  "/health": { target: API_TARGET, changeOrigin: true },
};

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy,
  },
  preview: {
    port: 4173,
    strictPort: true,
    proxy,
  },
});

