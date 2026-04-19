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
  heightPx: number;
  z: number;
  bottomPx: number;
};

// Slots for a 3-character party. Left% values ramp so members
// overlap; the middle one is taller and sits in front (higher z) to
// lead the eye.
// Left party — characters read left-to-right, tallest in the middle
// with the highest z-index so it leads the eye.
const LEFT_PARTY_SLOTS: SlotStyle[] = [
  { left: "0%", heightPx: 420, z: 1, bottomPx: 0 },
  { left: "22%", heightPx: 470, z: 3, bottomPx: -10 },
  { left: "50%", heightPx: 410, z: 2, bottomPx: 4 },
];

// Right party — tuned independently rather than mirrored off the left,
// because mirror math tightly couples left tweaks to right behavior
// and the visual centering looks different on each side. Same shape
// (3 members, tall middle) but hand-placed for balance.
const RIGHT_PARTY_SLOTS: SlotStyle[] = [
  { left: "-6%", heightPx: 410, z: 2, bottomPx: 4 },
  { left: "15%", heightPx: 470, z: 3, bottomPx: -10 },
  { left: "42%", heightPx: 420, z: 1, bottomPx: 0 },
];

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
      <div className="absolute left-0 bottom-0 w-[26%] h-[490px]">
        {leftParty.map((p, i) => (
          <PartyMember
            key={`${p.name}-${p.realm}-L`}
            player={p}
            slot={LEFT_PARTY_SLOTS[i]}
          />
        ))}
      </div>
      <div className="absolute right-0 bottom-0 w-[26%] h-[490px]">
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

  return (
    <div
      className="absolute opacity-40"
      style={{
        left: slot.left,
        bottom: `${slot.bottomPx}px`,
        height: `${slot.heightPx}px`,
        width: `${slot.heightPx * 0.6}px`,
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
