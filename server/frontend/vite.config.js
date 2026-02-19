import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/agents": { target: "http://localhost:8000", changeOrigin: true },
      "/farms": { target: "http://localhost:8000", changeOrigin: true },
      "/miners": { target: "http://localhost:8000", changeOrigin: true },
      "/health": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
