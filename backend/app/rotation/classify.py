"""Apply spec-aware classification to a raw rotation payload.

The raw payload stored on DungeonRun.rotation_events looks like:

    {
      "abilities": {"23881": {"name": "Bloodthirst", "icon": "..."}, ...},
      "casts": [{"t": 1.2, "s": 23881}, ...],
      "fight_start_ms": 123...
    }

Classification layers three transforms on top, keyed by the run's
(class_id, spec_name):

  1. Alias merge  — fragmented spell IDs (Odyn's Fury's four variants)
     collapse onto their canonical ID.
  2. Ignore filter — trinket procs, dungeon items, racials drop out
     entirely so the frequency table only shows real rotation/utility
     decisions.
  3. Category tag — each surviving ability gets "rotation" / "cooldown"
     / "utility" / "unknown" so the frontend can group them.

Classification is applied at response time, not during cache write, so
improvements to per-spec data (adding aliases, fixing an opener)
immediately propagate to every previously-cached run without needing a
cache flush.
"""
from app.rotation.registry import get_spec_data
from app.rotation.spec_data import classify, resolve_alias


def apply_classification(
    raw: dict, *, class_id: int, spec_name: str
) -> dict:
    """Return the enriched shape consumed by the /rotation response.

    Keys in the returned dict line up with RunRotationResponse fields:
    abilities, casts, classified, spec_key, reference_opener, guide_url.
    """
    abilities_in: dict = raw.get("abilities") or {}
    casts_in: list = raw.get("casts") or []
    spec = get_spec_data(class_id, spec_name)

    if spec is None:
        # No curated data yet for this spec — pass through as
        # unclassified. UI falls back to the Phase 1 layout.
        abilities_out = {
            k: {
                "name": v.get("name"),
                "icon": v.get("icon"),
                "category": "unknown",
            }
            for k, v in abilities_in.items()
        }
        casts_out = [
            {"t": c.get("t"), "s": c.get("s"), "cat": "unknown"}
            for c in casts_in
            if isinstance(c.get("s"), int)
        ]
        return {
            "abilities": abilities_out,
            "casts": casts_out,
            "classified": False,
            "spec_key": None,
            "reference_opener": None,
            "guide_url": None,
        }

    abilities_out: dict[str, dict] = {}
    casts_out: list[dict] = []
    # One button press on an aliased ability (Odyn's Fury) triggers
    # several combat-log events in quick succession — the main-hand hit,
    # the off-hand hit, and any bonus procs all land within ~0.4s of
    # the initial press. The player pressed the button once and should
    # see one timeline entry. Track the last-emitted timestamp per
    # canonical ID so we can skip fragment follow-ups within this
    # window. Canonicals that are NOT in the alias target set (i.e.
    # the "real" press event) always pass through regardless of recent
    # emits, so rapid back-to-back presses on non-aliased abilities
    # (Bloodthirst, Rampage) aren't wrongly collapsed.
    FRAGMENT_DEDUP_WINDOW_S = 1.0
    last_emit_t_by_canonical: dict[int, float] = {}

    for cast in casts_in:
        raw_id = cast.get("s")
        t = cast.get("t")
        if not isinstance(raw_id, int) or not isinstance(t, (int, float)):
            continue
        canonical = resolve_alias(spec, raw_id)
        if canonical in spec.ignore_ids:
            continue
        # Fragment dedup — only engages when this cast's raw ID is a
        # known alias fragment. Real presses on the canonical ID bypass
        # the check and emit normally.
        if raw_id in spec.aliases:
            last_t = last_emit_t_by_canonical.get(canonical)
            if last_t is not None and (t - last_t) < FRAGMENT_DEDUP_WINDOW_S:
                continue
        canonical_key = str(canonical)
        if canonical_key not in abilities_out:
            # Prefer metadata under the canonical ID (if WCL reported it
            # separately), fall back to the fragment's metadata. Either
            # way we end up with a sensible display name.
            meta = (
                abilities_in.get(canonical_key)
                or abilities_in.get(str(raw_id))
                or {}
            )
            abilities_out[canonical_key] = {
                "name": meta.get("name"),
                "icon": meta.get("icon"),
                "category": classify(spec, canonical),
            }
        casts_out.append({
            "t": t,
            "s": canonical,
            "cat": classify(spec, canonical),
        })
        last_emit_t_by_canonical[canonical] = t

    # Reference opener — icons pulled from the player's own abilities
    # map when available. Opener spells the player actually pressed will
    # have their real icon; spells the player skipped won't, and the
    # frontend falls back to a spell-ID chip.
    reference_opener = []
    for step in spec.reference_opener:
        meta = abilities_out.get(str(step.spell_id)) or {}
        reference_opener.append({
            "spell_id": step.spell_id,
            "name": step.name,
            "icon": step.icon or meta.get("icon"),
            "note": step.note,
        })

    return {
        "abilities": abilities_out,
        "casts": casts_out,
        "classified": True,
        "spec_key": spec.key,
        "reference_opener": reference_opener,
        "guide_url": spec.guide_url,
    }
