import { defineConfig } from "vitest/config";

export default defineConfig({
  esbuild: { jsx: "automatic" },          // permite escribir JSX sin importar React
  test: {
    environment: "jsdom",
    setupFiles: ["./setup.js"],
    globals: false,
    reporters: ["verbose"],
  },
});
