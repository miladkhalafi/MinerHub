import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/auth": { target: "http://localhost:8000", changeOrigin: true },
      "/users": { target: "http://localhost:8000", changeOrigin: true },
      "/agents": { target: "http://localhost:8000", changeOrigin: true },
      "/farms": { target: "http://localhost:8000", changeOrigin: true },
      "/miners": { target: "http://localhost:8000", changeOrigin: true },
      "/metrics": { target: "http://localhost:8000", changeOrigin: true },
      "/health": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
