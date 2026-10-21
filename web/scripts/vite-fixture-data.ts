// Vite plugin: serve a data version folder at /data/ (dev and preview) and copy it into the build.
// Milestone 1 serves the contract fixtures (contracts/fixtures/data); public/config.json decides which base URL
// the app reads, so switching to the published GitHub Pages / Hugging Face versions needs no rebuild.
import { cpSync, existsSync, readFileSync, statSync } from "node:fs";
import { extname, join, normalize, resolve } from "node:path";

import type { Connect, Plugin } from "vite";

const TYPES: Record<string, string> = {
  ".json": "application/json",
  ".geojson": "application/geo+json",
  ".jpg": "image/jpeg",
  ".png": "image/png",
  ".pmtiles": "application/octet-stream",
};

export function fixtureData(dir: string, mount = "/data/"): Plugin {
  const root = resolve(dir);
  let outDir = "dist";
  const serve: Connect.NextHandleFunction = (req, res, next) => {
    const path = decodeURIComponent(req.url?.split("?")[0] ?? "");
    if (!path.startsWith(mount)) return next();
    const file = normalize(join(root, path.slice(mount.length)));
    if (!file.startsWith(root) || !existsSync(file) || !statSync(file).isFile()) return next();
    res.setHeader("Content-Type", TYPES[extname(file)] ?? "application/octet-stream");
    res.end(readFileSync(file));
  };
  return {
    name: "plumes-fixture-data",
    configResolved: (c) => void (outDir = resolve(c.root, c.build.outDir)),
    configureServer: (server) => void server.middlewares.use(serve),
    configurePreviewServer: (server) => void server.middlewares.use(serve),
    closeBundle() {
      if (existsSync(outDir)) cpSync(root, join(outDir, mount), { recursive: true });
    },
  };
}
