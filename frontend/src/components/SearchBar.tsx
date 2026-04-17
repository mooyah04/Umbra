"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { searchPlayers } from "@/lib/api";
import type { PlayerSearchResult } from "@/lib/types";
import { getGradeColor } from "@/lib/grades";

export default function SearchBar() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PlayerSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const VALID_REGIONS = new Set(["us", "eu", "kr", "tw", "cn"]);

  /**
   * Parse a `Name-Realm-Region` string (or `Name-Realm Name-Region` with
   * a spaced realm) into a route target. The trailing token must be a
   * known region code; realm can contain hyphens (Area-52) so we join
   * everything between the first and last segments.
   */
  function parseIdentity(input: string): { name: string; realm: string; region: string } | null {
    const parts = input.trim().split("-").map((s) => s.trim()).filter(Boolean);
    if (parts.length < 3) return null;
    const region = parts[parts.length - 1].toLowerCase();
    if (!VALID_REGIONS.has(region)) return null;
    const name = parts[0];
    const realm = parts.slice(1, -1).join("-");
    if (!name || !realm) return null;
    return { name, realm, region };
  }

  async function handleSearch(value: string) {
    setQuery(value);
    if (value.length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }
    setLoading(true);
    try {
      const data = await searchPlayers(value);
      setResults(data);
      setOpen(true);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key !== "Enter") return;
    const parsed = parseIdentity(query);
    if (parsed) {
      // Looked like Name-Realm-Region — skip autocomplete, go straight in.
      e.preventDefault();
      setOpen(false);
      setQuery("");
      router.push(
        `/player/${parsed.region}/${encodeURIComponent(parsed.realm)}/${encodeURIComponent(parsed.name)}`,
      );
    } else if (results.length > 0) {
      // Otherwise enter picks the top autocomplete match.
      e.preventDefault();
      selectPlayer(results[0]);
    }
  }

  function selectPlayer(player: PlayerSearchResult) {
    setOpen(false);
    setQuery("");
    router.push(
      `/player/${player.region.toLowerCase()}/${player.realm.toLowerCase()}/${player.name.toLowerCase()}`,
    );
  }

  return (
    <div className="w-full max-w-3xl relative group">
      {/* Glow effect */}
      <div className="absolute -inset-0.5 bg-gradient-to-r from-primary to-primary-container opacity-20 blur group-focus-within:opacity-40 transition-opacity" />

      {/* Search input */}
      <div className="relative flex items-center bg-surface-container-highest h-16 md:h-20 px-6 rounded-lg">
        <span className="material-symbols-outlined text-on-surface-variant mr-4">
          search
        </span>
        <input
          type="text"
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => results.length > 0 && setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 200)}
          placeholder="Enter Name-Realm-Region (e.g. Elonmunk-Tarren Mill-EU)"
          className="bg-transparent border-none focus:ring-0 focus:outline-none w-full font-[family-name:var(--font-label)] text-lg md:text-xl placeholder:text-on-surface-variant/40 text-on-surface"
        />
        {loading ? (
          <span className="font-[family-name:var(--font-label)] text-xs text-on-surface-variant">
            ...
          </span>
        ) : (
          <kbd className="hidden md:flex items-center gap-1 font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant border border-outline-variant px-2 py-1 rounded">
            <span className="material-symbols-outlined text-sm">keyboard_command_key</span>
            K
          </kbd>
        )}
      </div>

      {/* Autocomplete dropdown */}
      {open && results.length > 0 && (
        <div className="absolute top-full mt-1 w-full bg-surface-container-highest border border-outline-variant rounded-lg shadow-xl overflow-hidden z-50">
          {results.map((player) => (
            <button
              key={`${player.name}-${player.realm}-${player.region}`}
              onClick={() => selectPlayer(player)}
              className="w-full px-6 py-4 flex items-center justify-between hover:bg-surface-bright transition-colors text-left"
            >
              <div className="flex items-center gap-3">
                <div>
                  <span className="font-[family-name:var(--font-headline)] font-bold text-on-surface">
                    {player.name}
                  </span>
                  <span className="text-on-surface-variant ml-2 font-[family-name:var(--font-label)] text-xs">
                    {player.realm}
                  </span>
                </div>
                <span className="text-[10px] font-[family-name:var(--font-label)] px-1 border border-primary/20 text-primary uppercase">
                  {player.region}
                </span>
              </div>
              <div className="flex items-center gap-3">
                {player.spec && (
                  <span className="font-[family-name:var(--font-label)] text-xs text-on-surface-variant">
                    {player.spec}
                  </span>
                )}
                {player.grade && (
                  <span
                    className="font-[family-name:var(--font-headline)] font-bold text-xl"
                    style={{ color: getGradeColor(player.grade) }}
                  >
                    {player.grade}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
