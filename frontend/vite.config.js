import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      // En dev local (npm run dev), redirige les appels /api vers le
      // backend FastAPI. En prod (Docker), c'est nginx qui joue ce role
      // (voir frontend/nginx.conf) -- le code frontend appelle toujours
      // simplement "/api/...", peu importe l'environnement.
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
