import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/pantry": "http://127.0.0.1:5000",
      "/low-stock": "http://127.0.0.1:5000",
      "/add-stock": "http://127.0.0.1:5000",
      "/upload-bill": "http://127.0.0.1:5000",
      "/import-sales-summary": "http://127.0.0.1:5000",
      "/dashboard-summary": "http://127.0.0.1:5000",
      "/report-insights": "http://127.0.0.1:5000"
    }
  },
  build: {
    outDir: "dist",
    emptyOutDir: true
  }
});
