import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(import.meta.dirname, "src") } },
  build: { chunkSizeWarningLimit: 800 },
  server: {
    // Khi chạy `npm run dev`, chuyển các request /api sang backend Python.
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
