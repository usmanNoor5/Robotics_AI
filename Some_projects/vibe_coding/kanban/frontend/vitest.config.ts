import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    tsconfigPaths: true,
  },
  test: {
    exclude: ["tests/**", "node_modules/**"],
    environment: "jsdom",
    globals: true,
    setupFiles: ["./test/setup.ts"],
  },
});
