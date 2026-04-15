/**
 * External WoW asset URLs. We don't bundle Blizzard artwork — we link to
 * Wowhead's CDN (wow.zamimg.com) which serves class icons + spell icons
 * publicly and is the standard for WoW fan sites. No auth / API key
 * required.
 *
 * If we later want 3D character portraits we'd have to integrate with
 * Blizzard's official Game Data API (OAuth client credentials) — that's
 * a separate, bigger workstream.
 */

/** Class icon filename by class_id. Lowercase, no spaces. */
const CLASS_ICON_SLUG: Record<number, string> = {
  1: "warrior",
  2: "paladin",
  3: "hunter",
  4: "rogue",
  5: "priest",
  6: "deathknight",
  7: "shaman",
  8: "mage",
  9: "warlock",
  10: "monk",
  11: "druid",
  12: "demonhunter",
  13: "evoker",
};

/**
 * Returns a 56×56 class icon URL. Used for player cards, search results,
 * and the breakdown page.
 */
export function classIconUrl(classId: number): string {
  const slug = CLASS_ICON_SLUG[classId] ?? "warrior";
  return `https://wow.zamimg.com/images/wow/icons/large/classicon_${slug}.jpg`;
}

/**
 * Returns a large 64×64 spec icon by spec name. Falls back to class icon
 * when a spec isn't in the map. Covers Midnight S1's active specs.
 */
const SPEC_ICON: Record<string, string> = {
  // Warrior
  Arms: "ability_warrior_savageblow",
  Fury: "ability_warrior_innerrage",
  "Protection": "ability_warrior_defensivestance",
  // Paladin
  Holy: "spell_holy_holybolt",
  Retribution: "spell_holy_auraoflight",
  // Hunter
  "Beast Mastery": "ability_hunter_bestialdiscipline",
  Marksmanship: "ability_hunter_focusedaim",
  Survival: "ability_hunter_swiftstrike",
  // Rogue
  Assassination: "ability_rogue_eviscerate",
  Outlaw: "ability_rogue_waylay",
  Subtlety: "ability_stealth",
  // Priest
  Discipline: "spell_holy_powerwordshield",
  Shadow: "spell_shadow_shadowwordpain",
  // Death Knight
  Blood: "spell_deathknight_bloodpresence",
  Frost: "spell_deathknight_frostpresence",
  Unholy: "spell_deathknight_unholypresence",
  // Shaman
  Elemental: "spell_nature_lightning",
  Enhancement: "spell_shaman_improvedstormstrike",
  Restoration: "spell_nature_magicimmunity",
  // Mage
  Arcane: "spell_holy_magicalsentry",
  Fire: "spell_fire_firebolt02",
  // Warlock
  Affliction: "spell_shadow_deathcoil",
  Demonology: "spell_shadow_metamorphosis",
  Destruction: "spell_shadow_rainoffire",
  // Monk
  Brewmaster: "spell_monk_brewmaster_spec",
  Mistweaver: "spell_monk_mistweaver_spec",
  Windwalker: "spell_monk_windwalker_spec",
  // Druid
  Balance: "spell_nature_starfall",
  Feral: "ability_druid_catform",
  Guardian: "ability_racial_bearform",
  // Demon Hunter
  Havoc: "ability_demonhunter_specdps",
  Vengeance: "ability_demonhunter_spectank",
  // Evoker
  Devastation: "classicon_evoker_devastation",
  Preservation: "classicon_evoker_preservation",
  Augmentation: "classicon_evoker_augmentation",
};

export function specIconUrl(specName: string | null | undefined, classId: number): string {
  if (!specName) return classIconUrl(classId);
  const icon = SPEC_ICON[specName];
  if (!icon) return classIconUrl(classId);
  return `https://wow.zamimg.com/images/wow/icons/large/${icon}.jpg`;
}
