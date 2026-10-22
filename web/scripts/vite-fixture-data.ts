// Vite plugin for tests and offline development: with PLUMES_FIXTURES=1, `vite` and `vite preview` serve the
// contract fixtures (contracts/fixtures/data) at /data/ and answer /config.json with a copy of public/config.json
// whose data base URL is /data/. The production build never contains the fixtures: the deployed public/config.json
// points at the published versions (GitHub Pages, Hugging Face mirror).
import { existsSync, readFileSync, statSync } from "node:fs";
import { extname, join, normalize, resolve } from "node:path";

import type { Connect, Plugin } from "vite";

const TYPES: Record<string, string> = {
  ".json": "application/json",
  ".geojson": "application/geo+json",
  ".jpg": "image/jpeg",
  ".png": "image/png",
  ".pmtiles": "application/octet-stream",
};

export function fixtureData(dir: string, { enabled = process.env.PLUMES_FIXTURES === "1", mount = "/data/" } = {}): Plugin {
  const root = resolve(dir);
  let publicDir = "public";
  const serve: Connect.NextHandleFunction = (req, res, next) => {
    const path = decodeURIComponent(req.url?.split("?")[0] ?? "");
    if (path === "/config.json") {
      const config = JSON.parse(readFileSync(join(publicDir, "config.json"), "utf8")) as { data: Record<string, unknown> };
      config.data = { ...config.data, baseUrl: mount, fallbackBaseUrls: [] };
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify(config));
      return;
    }
    if (!path.startsWith(mount)) return next();
    const file = normalize(join(root, path.slice(mount.length)));
    if (!file.startsWith(root) || !existsSync(file) || !statSync(file).isFile()) return next();
    res.setHeader("Content-Type", TYPES[extname(file)] ?? "application/octet-stream");
    res.end(readFileSync(file));
  };
  return {
    name: "plumes-fixture-data",
    configResolved: (c) => void (publicDir = c.publicDir || resolve(c.root, "public")),
    configureServer: (server) => void (enabled && server.middlewares.use(serve)),
    configurePreviewServer: (server) => void (enabled && server.middlewares.use(serve)),
  };
}
