"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

interface Realm {
  slug: string;
  name: string;
}

interface RealmsData {
  us: Realm[];
  eu: Realm[];
  kr: Realm[];
  tw: Realm[];
}

type Region = "us" | "eu" | "kr" | "tw";

const REGION_OPTIONS: Array<{ value: Region; label: string }> = [
  { value: "us", label: "US" },
  { value: "eu", label: "EU" },
  { value: "kr", label: "KR" },
  { value: "tw", label: "TW" },
];

export default function SearchBar() {
  const router = useRouter();
  const [realms, setRealms] = useState<RealmsData | null>(null);
  const [region, setRegion] = useState<Region | "">("");
  const [realmSlug, setRealmSlug] = useState("");
  const [name, setName] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetch("/realms.json")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!cancelled) setRealms(d as RealmsData | null);
      })
      .catch(() => setRealms(null));
    return () => {
      cancelled = true;
    };
  }, []);

  // Reset downstream fields when an earlier field changes.
  function handleRegionChange(v: Region | "") {
    setRegion(v);
    setRealmSlug("");
    setName("");
  }
  function handleRealmChange(v: string) {
    setRealmSlug(v);
    setName("");
  }

  const currentRealms = useMemo(() => {
    if (!region || !realms) return [];
    return realms[region] ?? [];
  }, [region, realms]);

  const canSubmit = region !== "" && realmSlug !== "" && name.trim().length > 0;

  function submit() {
    if (!canSubmit) return;
    router.push(
      `/player/${region}/${encodeURIComponent(realmSlug)}/${encodeURIComponent(
        name.trim(),
      )}`,
    );
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="w-full max-w-3xl relative group">
      {/* Glow effect on focus (same purple halo as before). */}
      <div className="absolute -inset-0.5 bg-gradient-to-r from-primary to-primary-container opacity-20 blur group-focus-within:opacity-40 transition-opacity pointer-events-none rounded-lg" />

      <div className="relative flex flex-col md:flex-row items-stretch bg-surface-container-highest rounded-lg overflow-hidden">
        {/* Region */}
        <select
          value={region}
          onChange={(e) => handleRegionChange(e.target.value as Region | "")}
          className="bg-transparent border-none focus:ring-0 focus:outline-none px-4 py-4 md:py-0 md:h-20 font-[family-name:var(--font-label)] text-sm text-on-surface uppercase tracking-widest md:border-r border-outline-variant/10 cursor-pointer"
          aria-label="Region"
        >
          <option value="">Region</option>
          {REGION_OPTIONS.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </select>

        {/* Server */}
        <select
          value={realmSlug}
          onChange={(e) => handleRealmChange(e.target.value)}
          disabled={!region || currentRealms.length === 0}
          className="bg-transparent border-none focus:ring-0 focus:outline-none px-4 py-4 md:py-0 md:h-20 font-[family-name:var(--font-label)] text-sm text-on-surface md:border-r border-outline-variant/10 md:max-w-[240px] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          aria-label="Server"
        >
          <option value="">
            {!region
              ? "Select region first"
              : currentRealms.length === 0
              ? "Loading..."
              : "Server"}
          </option>
          {currentRealms.map((r) => (
            <option key={r.slug} value={r.slug}>
              {r.name}
            </option>
          ))}
        </select>

        {/* Name */}
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={!realmSlug}
          placeholder={
            !region
              ? "Character name"
              : !realmSlug
              ? "Pick a server"
              : "Character name"
          }
          className="bg-transparent border-none focus:ring-0 focus:outline-none w-full px-4 py-4 md:py-0 md:h-20 font-[family-name:var(--font-label)] text-lg placeholder:text-on-surface-variant/40 text-on-surface disabled:opacity-40 disabled:cursor-not-allowed"
          aria-label="Character name"
        />

        {/* Submit */}
        <button
          onClick={submit}
          disabled={!canSubmit}
          className="shrink-0 h-12 md:h-20 md:w-24 m-2 md:m-0 bg-primary text-on-primary font-[family-name:var(--font-label)] text-xs uppercase tracking-widest flex items-center justify-center gap-2 hover:brightness-110 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          aria-label="Search"
        >
          <span className="material-symbols-outlined text-base">search</span>
          <span className="md:hidden">Search</span>
        </button>
      </div>

      {!realms && (
        <p className="absolute -bottom-6 left-2 text-xs text-on-surface-variant/70">
          Loading server list...
        </p>
      )}
    </div>
  );
}
