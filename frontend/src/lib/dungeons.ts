/**
 * Midnight Season 1 encounter_id → dungeon name. Mirrors the
 * backend's app/scoring/dungeons/ registry. Update when seasons roll.
 *
 * Two Midnight-expansion dungeons (Windrunner Spire, Skyreach) still
 * have unknown encounter IDs at the time of writing — we'll populate
 * those once we see one in a real log and can confirm the ID. Falls
 * back to "Mythic+ Dungeon" gracefully.
 */
export const DUNGEON_NAMES: Record<number, string> = {
  10658: "Pit of Saron",
  12811: "Magister's Terrace",
  12874: "Maisara Caverns",
  12915: "Nexus-Point Xenas",
  361753: "The Seat of the Triumvirate",
  112526: "Algeth'ar Academy",
  // TODO: Windrunner Spire, Skyreach — encounter IDs TBC
};

export function dungeonName(encounterId: number | null | undefined): string {
  if (encounterId == null) return "Mythic+ Dungeon";
  return DUNGEON_NAMES[encounterId] ?? "Mythic+ Dungeon";
}
