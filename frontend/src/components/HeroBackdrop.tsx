import type { PlayerSearchResult } from "@/lib/types";

/**
 * Decorative graded-character renders flanking the homepage hero.
 *
 * Pulls from the top-players feed (already fetched on the homepage),
 * places a few heavily-blurred insets on either side of the search
 * column. Purely aesthetic: self-updates as the graded pool grows,
 * no external art pipeline, and the "real people get graded here"
 * framing doubles as social proof.
 *
 * Hidden on mobile — the sidebar space that makes this work doesn't
 * exist below md.
 */
// Layered party composition — each member is absolutely positioned
// inside its side column and sits in front of or behind neighbors via
// z-index so the group reads as a huddle, not a police lineup. Left%
// values overlap (each ~35-40% apart) so characters look shoulder-to-
// shoulder; heights vary slightly for depth.
type SlotStyle = {
  left: string;
  heightMax: number;   // px at wide viewports
  heightPref: string;  // CSS expression that scales with viewport
  heightMin: number;   // px floor so characters never vanish entirely
  z: number;
  bottomPx: number;
};

// Slots for a 3-character party. Left% values ramp so members
// overlap; the middle one is taller and sits in front (higher z) to
// lead the eye. Heights use clamp() so the party scales down on
// narrower viewports instead of clipping — key to keeping the
// characters wholly inside their shrunken side column.
const LEFT_PARTY_SLOTS: SlotStyle[] = [
  { left: "0%",  heightMax: 420, heightPref: "22vw", heightMin: 300, z: 1, bottomPx: 0  },
  { left: "22%", heightMax: 470, heightPref: "25vw", heightMin: 335, z: 3, bottomPx: -10 },
  { left: "50%", heightMax: 410, heightPref: "22vw", heightMin: 290, z: 2, bottomPx: 4  },
];

// Right party — tuned independently rather than mirrored off the left,
// because mirror math tightly couples left tweaks to right behavior
// and the visual centering looks different on each side. Same shape
// (3 members, tall middle) but hand-placed for balance.
const RIGHT_PARTY_SLOTS: SlotStyle[] = [
  { left: "-6%", heightMax: 410, heightPref: "22vw", heightMin: 290, z: 2, bottomPx: 4  },
  { left: "15%", heightMax: 470, heightPref: "25vw", heightMin: 335, z: 3, bottomPx: -10 },
  { left: "42%", heightMax: 420, heightPref: "22vw", heightMin: 300, z: 1, bottomPx: 0  },
];

// Half-width of the search bar (max-w-3xl = 768px / 2 = 384px) plus a
// visual breathing gutter. The side columns must never cross the line
// `50vw - SEARCH_SAFE_ZONE_PX`, or a character bleeds into the search
// input's footprint. 24px of gutter keeps the art decisively off the
// widget rather than kissing its edge.
const SEARCH_SAFE_ZONE_PX = 384 + 24;

// Dynamic column width: 26vw where there's room, collapses toward 0 on
// viewports too narrow to host both the search bar and a character
// gallery. The max(0px, ...) guard keeps the calc valid at extreme
// widths where the inner expression would go negative.
const SIDE_COLUMN_WIDTH = `min(26vw, max(0px, calc(50vw - ${SEARCH_SAFE_ZONE_PX}px)))`;

export default function HeroBackdrop({
  players,
}: {
  players: PlayerSearchResult[];
}) {
  const withImage = players.filter((p) => p.inset_url);
  // Shuffle the pool so the hero isn't always populated by the same
  // characters. The homepage renders with ISR (revalidate: 15), so
  // each cache miss produces a new random party — visitors arriving
  // minutes apart see different faces without needing client-side
  // randomization that would risk hydration mismatch.
  const pool = [...withImage];
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  const leftParty = pool.slice(0, LEFT_PARTY_SLOTS.length);
  const rightParty = pool.slice(
    LEFT_PARTY_SLOTS.length,
    LEFT_PARTY_SLOTS.length + RIGHT_PARTY_SLOTS.length,
  );

  if (leftParty.length === 0 && rightParty.length === 0) return null;

  return (
    <div
      aria-hidden
      // Break out of the centered max-w-7xl parent and span the full
      // viewport so the parties stand at the actual screen edges.
      className="hidden md:block pointer-events-none absolute top-0 bottom-0 left-1/2 -translate-x-1/2 w-screen overflow-hidden"
    >
      <div
        className="absolute left-0 bottom-0 h-[490px] overflow-hidden"
        style={{ width: SIDE_COLUMN_WIDTH }}
      >
        {leftParty.map((p, i) => (
          <PartyMember
            key={`${p.name}-${p.realm}-L`}
            player={p}
            slot={LEFT_PARTY_SLOTS[i]}
          />
        ))}
      </div>
      <div
        className="absolute right-0 bottom-0 h-[490px] overflow-hidden"
        style={{ width: SIDE_COLUMN_WIDTH }}
      >
        {rightParty.map((p, i) => (
          <PartyMember
            key={`${p.name}-${p.realm}-R`}
            player={p}
            slot={RIGHT_PARTY_SLOTS[i]}
          />
        ))}
      </div>
    </div>
  );
}

function PartyMember({
  player,
  slot,
}: {
  player: PlayerSearchResult;
  slot: SlotStyle;
}) {
  // Blizzard hosts three variants per character at predictable
  // suffixes: -avatar.jpg, -inset.jpg (with WoW backdrop), and
  // -main-raw.png (TRANSPARENT full-body render). Deriving the render
  // URL from inset_url avoids a backend schema change.
  const renderUrl = player.inset_url!.replace(
    /-inset\.jpg$/,
    "-main-raw.png",
  );

  // Height uses clamp(min, preferred-vw, max) so the character scales
  // with the viewport: full size on wide screens, proportionally
  // smaller on narrower ones. Width is 60% of the current height (the
  // aspect we used when the heights were hardcoded) via CSS calc so it
  // stays in lockstep as the height clamps.
  const heightExpr =
    `clamp(${slot.heightMin}px, ${slot.heightPref}, ${slot.heightMax}px)`;

  return (
    <div
      className="absolute opacity-40"
      style={{
        left: slot.left,
        bottom: `${slot.bottomPx}px`,
        height: heightExpr,
        width: `calc(${heightExpr} * 0.6)`,
        zIndex: slot.z,
      }}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={renderUrl}
        alt=""
        className="absolute inset-0 w-full h-full object-contain object-bottom"
      />
    </div>
  );
}
