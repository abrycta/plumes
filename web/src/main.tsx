import "./index.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "@/app/App";
import { prefetchFirstView } from "@/app/prefetch";

const root = document.getElementById("root");
if (!root) throw new Error("#root element missing from index.html");

// The first view's data (and, on rich-media screens, the map code) starts now, not after the page chunk arrives.
prefetchFirstView();

// Web fonts: a separate stylesheet so the @font-face rules never block the first paint.
void import("./fonts.css");

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
