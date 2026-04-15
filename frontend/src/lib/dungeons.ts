/**
 * Midnight Season 1 encounter_id → dungeon name. Mirrors the
 * backend's app/scoring/dungeons/ registry. Update when seasons roll.
 *
 * One Midnight-expansion dungeon (Windrunner Spire) still has an
 * unknown encounter ID at the time of writing — we'll populate it once
 * we see one in a real log and can confirm the ID. Falls back to
 * "Mythic+ Dungeon" gracefully.
 */
export const DUNGEON_NAMES: Record<number, string> = {
  10658: "Pit of Saron",
  12811: "Magister's Terrace",
  12874: "Maisara Caverns",
  12915: "Nexus-Point Xenas",
  61209: "Skyreach",
  361753: "The Seat of the Triumvirate",
  112526: "Algeth'ar Academy",
  // TODO: Windrunner Spire — encounter ID TBC
};

export function dungeonName(encounterId: number | null | undefined): string {
  if (encounterId == null) return "Mythic+ Dungeon";
  return DUNGEON_NAMES[encounterId] ?? "Mythic+ Dungeon";
}
