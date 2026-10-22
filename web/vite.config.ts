import { execSync } from "node:child_process";
import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

import { embedPack } from "./scripts/vite-embed-pack.ts";
import { mapPack } from "./scripts/vite-map-pack.ts";
import { preloadEmbed } from "./scripts/vite-preload-embed.ts";
import { fixtureData } from "./scripts/vite-fixture-data.ts";
import { akariThemeInit } from "./scripts/vite-theme-init.ts";

// Commit shown in the footer: CI sets BUILD_SHA or GITHUB_SHA; the local checkout is the fallback.
function commitSha(): string {
  const fromEnv = process.env.BUILD_SHA ?? process.env.GITHUB_SHA;
  if (fromEnv) return fromEnv;
  try {
    return execSync("git rev-parse HEAD", { stdio: ["ignore", "pipe", "ignore"] }).toString().trim();
  } catch {
    return "unknown";
  }
}

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    // Akari's pre-paint theme script (shared krtmtthw.dev theme cookie), served from our own origin.
    akariThemeInit(),
    // PLUMES_FIXTURES=1 (e2e, offline dev): the contract fixtures at /data/ and a config.json pointing there.
    fixtureData(fileURLToPath(new URL("../contracts/fixtures/data", import.meta.url))),
    // /embed's precomputed windows (small files instead of whole yearly layers), from the published data.
    embedPack(fileURLToPath(new URL("./public/config.json", import.meta.url))),
    // The map page's first window (map/firstWindow.ts): one small file instead of two yearly layers on first view.
    mapPack(fileURLToPath(new URL("./public/config.json", import.meta.url))),
    // /embed: the map chunk, its worker and the pack index preloaded from embed.html.
    preloadEmbed(),
  ],
  define: {
    __COMMIT_SHA__: JSON.stringify(commitSha()),
  },
  resolve: {
    alias: {
      "@contracts": fileURLToPath(new URL("../contracts/ts", import.meta.url)),
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
    dedupe: ["react", "react-dom"],
  },
  // MapLibre 6 resolves its worker file relative to its own module; pre-bundling breaks that in dev.
  optimizeDeps: { exclude: ["maplibre-gl"] },
  build: {
    outDir: "dist",
    assetsDir: "assets",
    sourcemap: true,
    target: "es2023",
    // Never inline fonts as data: URIs. Akari's @font-face rules split each face into many unicode-range subsets;
    // inlined, the small ones (58 of them) made fonts.css about 290 kB gzipped and were all downloaded whether or not
    // the page uses those characters. As files, the browser fetches only the subsets a page needs.
    assetsInlineLimit: (file) => (/\.(woff2?|ttf|otf)$/.test(file) ? false : undefined),
    chunkSizeWarningLimit: 1100, // maplibre-gl is one ~1 MB chunk, loaded only with the interactive map
    // Two pages, one build: /embed (the view krtmtthw.dev frames) shares the app's hashed chunks.
    rollupOptions: { input: { main: "index.html", embed: "embed.html" } },
  },
  test: {
    include: ["src/**/*.test.{ts,tsx}"],
    environment: "node",
    maxWorkers: 2,
  },
});
