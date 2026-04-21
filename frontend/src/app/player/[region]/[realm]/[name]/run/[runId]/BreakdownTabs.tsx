"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { ApiError, getRunRotation } from "@/lib/api";
import type {
  Pull,
  ReferenceOpenerStep,
  RotationAbility,
  RotationCast,
  RotationCategory,
  RunRotationResponse,
} from "@/lib/types";

interface Props {
  region: string;
  realm: string;
  name: string;
  runId: number;
  /** Pre-rendered pull-by-pull section from the server component. Passed
   *  as JSX so the existing PullCard rendering stays put and we don't
   *  duplicate the grouping logic. */
  pullsContent: ReactNode;
  /** Raw pulls array — used by the rotation tab to segment the timeline
   *  by pull so users can see what they cast during each pack. Null if
   *  this run was ingested before Level B v2. */
  pulls: Pull[] | null;
}

type Tab = "pulls" | "rotation";
type LoadState = "idle" | "loading" | "error";

const OPENER_CAST_COUNT = 15;

/** Labels for the grouped frequency sections, in display order. Picked
 *  to read as a narrative: what you actually DPS'd with first, the big
 *  buttons that define the run second, kicks/defensives last. */
const CATEGORY_TITLES: Record<RotationCategory, string> = {
  rotation: "Rotation",
  cooldown: "Cooldowns",
  utility: "Utility",
  unknown: "Other",
};

const CATEGORY_ORDER: RotationCategory[] = [
  "rotation",
  "cooldown",
  "utility",
  "unknown",
];

export default function BreakdownTabs({
  region,
  realm,
  name,
  runId,
  pullsContent,
  pulls,
}: Props) {
  const [tab, setTab] = useState<Tab>("pulls");
  const [rotation, setRotation] = useState<RunRotationResponse | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [errorMsg, setErrorMsg] = useState<string>("");

  const switchTab = (next: Tab) => {
    setTab(next);
    if (next === "rotation" && rotation === null && loadState !== "loading") {
      setLoadState("loading");
      setErrorMsg("");
      getRunRotation(region, realm, name, runId)
        .then((r) => {
          setRotation(r);
          setLoadState("idle");
        })
        .catch((err: unknown) => {
          const msg =
            err instanceof ApiError
              ? err.message
              : err instanceof Error
                ? err.message
                : "Could not load rotation";
          setErrorMsg(msg);
          setLoadState("error");
        });
    }
  };

  return (
    <section className="space-y-4">
      <div className="flex items-end justify-between flex-wrap gap-3 border-b border-outline-variant/20 pb-2">
        <div className="flex gap-1">
          <TabButton
            active={tab === "pulls"}
            onClick={() => switchTab("pulls")}
            label="Pull-by-Pull"
          />
          <TabButton
            active={tab === "rotation"}
            onClick={() => switchTab("rotation")}
            label="Rotation"
          />
        </div>
        <p className="text-[10px] font-[family-name:var(--font-label)] uppercase tracking-[0.25em] text-on-surface-variant/70">
          {tab === "pulls"
            ? "What happened each pack"
            : "What you pressed and when"}
        </p>
      </div>

      {tab === "pulls" && pullsContent}
      {tab === "rotation" && (
        <RotationPanel
          state={loadState}
          errorMsg={errorMsg}
          data={rotation}
          pulls={pulls}
          onRetry={() => {
            setRotation(null);
            switchTab("rotation");
          }}
        />
      )}
    </section>
  );
}

function TabButton({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`font-[family-name:var(--font-label)] text-xs uppercase tracking-widest px-4 py-2 rounded-t transition-colors border-b-2 ${
        active
          ? "text-primary border-primary bg-surface-container-high/50"
          : "text-on-surface-variant border-transparent hover:text-on-surface hover:bg-surface-container/50"
      }`}
    >
      {label}
    </button>
  );
}

function RotationPanel({
  state,
  errorMsg,
  data,
  pulls,
  onRetry,
}: {
  state: LoadState;
  errorMsg: string;
  data: RunRotationResponse | null;
  pulls: Pull[] | null;
  onRetry: () => void;
}) {
  if (state === "loading") {
    return (
      <div className="bg-surface-container rounded-xl p-12 text-center">
        <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-widest text-on-surface-variant">
          Loading cast timeline from Warcraft Logs…
        </p>
        <p className="text-xs text-on-surface-variant/70 mt-2">
          First load fetches and caches the rotation. Future views are instant.
        </p>
      </div>
    );
  }

  if (state === "error") {
    return (
      <div className="bg-error-container/20 border border-error/30 rounded-xl p-6">
        <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-widest text-error mb-2">
          Could not load rotation
        </p>
        <p className="text-sm text-on-surface-variant mb-4">{errorMsg}</p>
        <button
          onClick={onRetry}
          className="font-[family-name:var(--font-label)] text-xs uppercase tracking-widest px-4 py-2 bg-primary text-on-primary rounded hover:bg-primary/80 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data || data.casts.length === 0) {
    return (
      <div className="bg-surface-container rounded-xl p-6">
        <p className="text-sm text-on-surface-variant">
          No cast events recorded for this run.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {!data.classified && <UnclassifiedNotice specName={data.spec_name} />}
      <OpenerStrip
        casts={data.casts}
        abilities={data.abilities}
        reference={data.reference_opener}
      />
      <FrequencyTable
        casts={data.casts}
        abilities={data.abilities}
        classified={data.classified}
      />
      <CastTimeline casts={data.casts} abilities={data.abilities} pulls={pulls} />
      <p className="text-[10px] font-[family-name:var(--font-label)] uppercase tracking-widest text-on-surface-variant/60 text-center">
        {data.cached
          ? "Served from cache"
          : "Freshly fetched — subsequent views are instant"}
      </p>
    </div>
  );
}

function UnclassifiedNotice({ specName }: { specName: string }) {
  return (
    <div className="bg-surface-container rounded-xl p-4 border-l-4 border-primary/40">
      <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-primary mb-1">
        Heads up
      </p>
      <p className="text-sm text-on-surface-variant">
        Rotation classification for <span className="font-semibold text-on-surface">{specName}</span> hasn&apos;t been curated yet — you&apos;ll see raw casts without
        rotation / cooldown / utility grouping or a reference opener.
        Coming soon.
      </p>
    </div>
  );
}

/** First N casts laid out horizontally. When reference data is present,
 *  renders the player's opener on top with the curated reference below
 *  so the user can see divergence at a glance. */
function OpenerStrip({
  casts,
  abilities,
  reference,
}: {
  casts: RotationCast[];
  abilities: Record<string, RotationAbility>;
  reference: ReferenceOpenerStep[] | null;
}) {
  const yourOpener = casts.slice(0, OPENER_CAST_COUNT);
  const refOpener = reference?.slice(0, OPENER_CAST_COUNT) ?? null;

  return (
    <div className="bg-surface-container-high rounded-xl p-6">
      <div className="flex items-end justify-between mb-4 flex-wrap gap-2">
        <div>
          <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-[0.3em] text-primary mb-1">
            Opener
          </p>
          <h3 className="font-[family-name:var(--font-headline)] font-extrabold text-xl tracking-tighter uppercase text-on-surface italic">
            {refOpener ? "Yours vs. recommended" : `First ${yourOpener.length} casts`}
          </h3>
        </div>
        {!refOpener && (
          <p className="text-[10px] font-[family-name:var(--font-label)] uppercase tracking-widest text-on-surface-variant max-w-xs text-right">
            Compare to your spec&apos;s opener on Icy Veins.
          </p>
        )}
      </div>
      <div className="space-y-4">
        <OpenerRow
          label="You"
          items={yourOpener.map((c, idx) => {
            const ab = abilities[String(c.s)];
            return {
              key: `you-${idx}`,
              spellId: c.s,
              name: ab?.name ?? `#${c.s}`,
              icon: ab?.icon ?? null,
              sub: formatClock(c.t),
            };
          })}
          accent="primary"
        />
        {refOpener && (
          <OpenerRow
            label="Guide"
            items={refOpener.map((s, idx) => ({
              key: `ref-${idx}`,
              spellId: s.spell_id,
              name: s.name,
              icon: s.icon,
              sub: s.note ?? "",
            }))}
            accent="secondary"
            muted
          />
        )}
      </div>
      {refOpener && (
        <p className="mt-4 text-[10px] font-[family-name:var(--font-label)] uppercase tracking-widest text-on-surface-variant/60">
          Recommended sequence is a guideline — real openers adapt to
          procs, movement, and trash packs.
        </p>
      )}
    </div>
  );
}

interface OpenerRowItem {
  key: string;
  spellId: number;
  name: string;
  icon: string | null;
  sub: string;
}

function OpenerRow({
  label,
  items,
  accent,
  muted,
}: {
  label: string;
  items: OpenerRowItem[];
  accent: "primary" | "secondary";
  muted?: boolean;
}) {
  const accentColor = accent === "primary" ? "text-primary" : "text-secondary";
  return (
    <div>
      <p
        className={`font-[family-name:var(--font-label)] text-[10px] uppercase tracking-[0.25em] mb-2 ${accentColor}`}
      >
        {label}
      </p>
      <ol className={`flex gap-2 overflow-x-auto pb-2 ${muted ? "opacity-90" : ""}`}>
        {items.length === 0 ? (
          <li className="text-xs italic text-on-surface-variant/60">
            No casts in the opener window.
          </li>
        ) : (
          items.map((it, idx) => (
            <li
              key={it.key}
              className="flex flex-col items-center gap-1 shrink-0 w-16"
            >
              <span className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant/70 tabular-nums">
                {idx + 1}
              </span>
              <SpellIcon
                spellId={it.spellId}
                ability={{ name: it.name, icon: it.icon, category: "unknown" }}
                size={44}
              />
              <span className="text-[9px] text-center text-on-surface-variant font-[family-name:var(--font-label)] leading-tight truncate w-full">
                {it.name}
              </span>
              {it.sub && (
                <span className="text-[9px] text-on-surface-variant/60 tabular-nums truncate w-full text-center">
                  {it.sub}
                </span>
              )}
            </li>
          ))
        )}
      </ol>
    </div>
  );
}

/** How often each ability was cast, sorted by frequency. When the
 *  player's spec has curated data, splits into Rotation / Cooldowns /
 *  Utility sections so the user can scan each role separately. */
function FrequencyTable({
  casts,
  abilities,
  classified,
}: {
  casts: RotationCast[];
  abilities: Record<string, RotationAbility>;
  classified: boolean;
}) {
  type Row = {
    spellId: number;
    count: number;
    pct: number;
    category: RotationCategory;
    ability: RotationAbility | undefined;
  };

  const counts = new Map<number, number>();
  for (const c of casts) counts.set(c.s, (counts.get(c.s) ?? 0) + 1);
  const total = casts.length;
  const rows: Row[] = [...counts.entries()]
    .map(([spellId, count]) => {
      const ability = abilities[String(spellId)];
      return {
        spellId,
        count,
        pct: total > 0 ? (count / total) * 100 : 0,
        category: ability?.category ?? "unknown",
        ability,
      };
    })
    .sort((a, b) => b.count - a.count);

  // Unclassified path — single flat list (Phase 1 behavior).
  if (!classified) {
    return (
      <div className="bg-surface-container-high rounded-xl p-6">
        <SectionHeader
          eyebrow="Cast Frequency"
          title={`${rows.length} abilities, ${total} total casts`}
        />
        <FrequencyList rows={rows} maxCount={rows[0]?.count ?? 1} />
      </div>
    );
  }

  // Classified path — group rows by category, render each section.
  const grouped: Record<RotationCategory, Row[]> = {
    rotation: [],
    cooldown: [],
    utility: [],
    unknown: [],
  };
  for (const row of rows) grouped[row.category].push(row);

  return (
    <div className="bg-surface-container-high rounded-xl p-6 space-y-6">
      <SectionHeader
        eyebrow="Cast Frequency"
        title="Grouped by ability type"
      />
      {CATEGORY_ORDER.map((cat) => {
        const sectionRows = grouped[cat];
        if (sectionRows.length === 0) return null;
        const sectionMax = sectionRows[0]?.count ?? 1;
        const sectionTotal = sectionRows.reduce((s, r) => s + r.count, 0);
        return (
          <div key={cat} className="space-y-2">
            <div className="flex items-baseline justify-between gap-2 flex-wrap">
              <p className="font-[family-name:var(--font-label)] text-[11px] uppercase tracking-[0.25em] text-primary">
                {CATEGORY_TITLES[cat]}
              </p>
              <p className="font-[family-name:var(--font-label)] text-[10px] tabular-nums text-on-surface-variant/70">
                {sectionRows.length} abilities ·{" "}
                {total > 0
                  ? `${((sectionTotal / total) * 100).toFixed(1)}% of casts`
                  : "—"}
              </p>
            </div>
            <FrequencyList rows={sectionRows} maxCount={sectionMax} />
          </div>
        );
      })}
    </div>
  );
}

function SectionHeader({
  eyebrow,
  title,
}: {
  eyebrow: string;
  title: string;
}) {
  return (
    <div>
      <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-[0.3em] text-primary mb-1">
        {eyebrow}
      </p>
      <h3 className="font-[family-name:var(--font-headline)] font-extrabold text-xl tracking-tighter uppercase text-on-surface italic">
        {title}
      </h3>
    </div>
  );
}

function FrequencyList({
  rows,
  maxCount,
}: {
  rows: Array<{
    spellId: number;
    count: number;
    pct: number;
    ability: RotationAbility | undefined;
  }>;
  maxCount: number;
}) {
  return (
    <ul className="space-y-1.5">
      {rows.map((r) => (
        <li
          key={r.spellId}
          className="flex items-center gap-3 bg-surface-container-highest/60 rounded px-3 py-2"
        >
          <SpellIcon spellId={r.spellId} ability={r.ability} size={28} />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-on-surface truncate font-[family-name:var(--font-body)]">
              {r.ability?.name ?? `Spell #${r.spellId}`}
            </p>
            <div className="mt-1 h-1 bg-surface-container rounded overflow-hidden">
              <div
                className="h-full bg-primary/60"
                style={{ width: `${(r.count / Math.max(1, maxCount)) * 100}%` }}
              />
            </div>
          </div>
          <div className="text-right tabular-nums shrink-0 w-20">
            <p className="text-sm font-bold text-on-surface">{r.count}x</p>
            <p className="text-[10px] text-on-surface-variant">
              {r.pct.toFixed(1)}%
            </p>
          </div>
        </li>
      ))}
    </ul>
  );
}

/** Horizontal timeline split by pull (when available) so the reader can
 *  see what the player pressed during each pack. Icons are positioned
 *  proportionally to cast time within the pull. */
function CastTimeline({
  casts,
  abilities,
  pulls,
}: {
  casts: RotationCast[];
  abilities: Record<string, RotationAbility>;
  pulls: Pull[] | null;
}) {
  const segments =
    pulls && pulls.length > 0
      ? pulls.map((p) => ({
          label: `Pull ${String(p.i).padStart(2, "0")} — ${p.label}`,
          start: p.start_t,
          end: p.end_t,
          casts: casts.filter((c) => c.t >= p.start_t && c.t < p.end_t),
        }))
      : [
          {
            label: "Full run",
            start: 0,
            end: casts[casts.length - 1]?.t ?? 0,
            casts,
          },
        ];

  return (
    <div className="bg-surface-container-high rounded-xl p-6">
      <SectionHeader eyebrow="Timeline" title="Cast order by pull" />
      <ol className="space-y-4 mt-4">
        {segments.map((seg, idx) => (
          <TimelineSegment
            key={idx}
            label={seg.label}
            start={seg.start}
            end={seg.end}
            casts={seg.casts}
            abilities={abilities}
          />
        ))}
      </ol>
    </div>
  );
}

function TimelineSegment({
  label,
  start,
  end,
  casts,
  abilities,
}: {
  label: string;
  start: number;
  end: number;
  casts: RotationCast[];
  abilities: Record<string, RotationAbility>;
}) {
  const duration = Math.max(1, end - start);
  return (
    <li className="space-y-2">
      <div className="flex items-baseline justify-between gap-3 flex-wrap">
        <span className="font-[family-name:var(--font-label)] text-[11px] uppercase tracking-widest text-on-surface/80 truncate">
          {label}
        </span>
        <span className="font-[family-name:var(--font-label)] text-[10px] tabular-nums text-on-surface-variant/70">
          {formatClock(start)}–{formatClock(end)} · {casts.length} casts
        </span>
      </div>
      <div className="flex gap-1 flex-wrap">
        {casts.length === 0 ? (
          <span className="text-xs italic text-on-surface-variant/50">
            No casts in this segment.
          </span>
        ) : (
          casts.map((c, i) => {
            const ability = abilities[String(c.s)];
            const offsetPct = ((c.t - start) / duration) * 100;
            return (
              <SpellIcon
                key={`${i}-${c.t}`}
                spellId={c.s}
                ability={ability}
                size={24}
                title={`${ability?.name ?? `#${c.s}`} @ ${formatClock(c.t)} (${offsetPct.toFixed(0)}% through pull)`}
              />
            );
          })
        )}
      </div>
    </li>
  );
}

/** Wowhead-hosted icon for a WoW ability. WCL's `icon` field returns
 *  the base file name (with or without extension); strip any extension
 *  and hit zamimg's large-icon CDN. Falls back to a spell-number chip
 *  when WCL didn't have an icon for the ability. Wraps in a link to
 *  the Wowhead spell page for detail. */
function SpellIcon({
  spellId,
  ability,
  size,
  title,
}: {
  spellId: number;
  ability: RotationAbility | undefined;
  size: number;
  title?: string;
}) {
  const href = `https://www.wowhead.com/spell=${spellId}`;
  const name = ability?.name ?? `Spell ${spellId}`;
  const hoverTitle = title ?? name;
  const iconUrl = spellIconUrl(ability?.icon ?? null);

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      title={hoverTitle}
      className="shrink-0 block hover:ring-2 hover:ring-primary/60 rounded transition-shadow"
      style={{ width: size, height: size }}
    >
      {iconUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={iconUrl}
          alt={name}
          width={size}
          height={size}
          className="rounded block"
        />
      ) : (
        <span
          className="flex items-center justify-center rounded bg-surface-container text-[9px] text-on-surface-variant font-[family-name:var(--font-label)]"
          style={{ width: size, height: size }}
        >
          #{spellId}
        </span>
      )}
    </a>
  );
}

function spellIconUrl(iconName: string | null): string | null {
  if (!iconName) return null;
  const clean = iconName.replace(/\.(jpg|png|webp)$/i, "").toLowerCase();
  if (!clean) return null;
  return `https://wow.zamimg.com/images/wow/icons/large/${clean}.jpg`;
}

function formatClock(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}
