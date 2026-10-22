// One /embed screen: a real app page at the frame's width and its own spacing (as Lights' embed shows its app), seen
// from a chosen place: the top of the page, the top of the element `at` (a section), or, with `align="bottom"`, the
// page's end (e.g. a chart under its intro). The page never scrolls; it is moved, and what lies past the frame is
// cut like a screenshot. It re-measures while the page's data arrives and when the frame resizes.
import { useEffect, useRef, useState, type ReactNode } from "react";

export function FitScreen({ children, at, align = "top" }: { children: ReactNode; at?: string; align?: "top" | "bottom" }) {
  const outer = useRef<HTMLDivElement>(null);
  const inner = useRef<HTMLDivElement>(null);
  const [y, setY] = useState<number | null>(null);
  useEffect(() => {
    const o = outer.current;
    const i = inner.current;
    if (!o || !i) return;
    const measure = () => {
      const H = o.clientHeight;
      if (!H) return;
      const base = i.offsetTop;
      const target = at ? i.querySelector<HTMLElement>(at) : null;
      let next = 0;
      if (align === "bottom") next = Math.min(0, H - i.scrollHeight);
      else if (target) {
        // The section's top a little below the frame's edge (its own spacing), never past the page's end.
        const top = target.getBoundingClientRect().top - i.getBoundingClientRect().top + base;
        next = -Math.max(0, Math.min(top - 16, i.scrollHeight - H));
      }
      setY((prev) => (prev === next ? prev : next));
    };
    measure();
    const timer = window.setInterval(measure, 400);
    const stop = window.setTimeout(() => clearInterval(timer), 15_000);
    const ro = new ResizeObserver(measure);
    ro.observe(o);
    return () => {
      clearInterval(timer);
      clearTimeout(stop);
      ro.disconnect();
    };
  }, [at, align]);
  return (
    <div ref={outer} className="absolute inset-0 overflow-hidden bg-background">
      <div ref={inner} className="absolute inset-x-0 top-0" style={y == null ? { visibility: "hidden" } : { transform: `translateY(${y}px)` }} data-fit-y={y ?? undefined}>
        {children}
      </div>
    </div>
  );
}
