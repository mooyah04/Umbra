"use client";

import { Children, isValidElement, useEffect, useRef, useState } from "react";

/**
 * Horizontal scroll-snap carousel for the Recently Graded section.
 * Wraps each child in a fixed-width snap cell so PlayerCard (or anything
 * else) can stay styling-agnostic. Arrows fade in/out depending on
 * scroll position; pure CSS scroll + a single `scrollBy` call per click,
 * no animation dependencies.
 */
export default function RecentlyGradedCarousel({
  children,
}: {
  children: React.ReactNode;
}) {
  const scroller = useRef<HTMLDivElement>(null);
  const [canLeft, setCanLeft] = useState(false);
  const [canRight, setCanRight] = useState(true);

  function updateArrows() {
    const el = scroller.current;
    if (!el) return;
    setCanLeft(el.scrollLeft > 8);
    setCanRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 8);
  }

  useEffect(() => {
    updateArrows();
    const el = scroller.current;
    if (!el) return;
    const onResize = () => updateArrows();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  function scroll(dir: -1 | 1) {
    const el = scroller.current;
    if (!el) return;
    // Scroll by ~one card-width; small enough to feel responsive, large
    // enough to feel like real paging. 296 = 280 card + 16 gap.
    el.scrollBy({ left: dir * 296, behavior: "smooth" });
  }

  return (
    <div className="relative">
      <div
        ref={scroller}
        onScroll={updateArrows}
        className="overflow-x-auto scroll-smooth snap-x snap-mandatory pb-3 [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden"
      >
        <div className="flex gap-4">
          {Children.map(children, (child, i) =>
            isValidElement(child) ? (
              <div key={i} className="w-[280px] shrink-0 snap-start">
                {child}
              </div>
            ) : null,
          )}
        </div>
      </div>

      <button
        type="button"
        onClick={() => scroll(-1)}
        aria-label="Scroll left"
        disabled={!canLeft}
        className={`absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 z-10 hidden md:flex w-10 h-10 rounded-full bg-surface-container-high border border-outline-variant/30 items-center justify-center shadow-lg transition-opacity ${
          canLeft
            ? "opacity-100 hover:bg-surface-bright"
            : "opacity-0 pointer-events-none"
        }`}
      >
        <span className="material-symbols-outlined text-on-surface">
          chevron_left
        </span>
      </button>
      <button
        type="button"
        onClick={() => scroll(1)}
        aria-label="Scroll right"
        disabled={!canRight}
        className={`absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 z-10 hidden md:flex w-10 h-10 rounded-full bg-surface-container-high border border-outline-variant/30 items-center justify-center shadow-lg transition-opacity ${
          canRight
            ? "opacity-100 hover:bg-surface-bright"
            : "opacity-0 pointer-events-none"
        }`}
      >
        <span className="material-symbols-outlined text-on-surface">
          chevron_right
        </span>
      </button>
    </div>
  );
}
