"""Rotation spec registry — loads curated per-spec modules and exposes
lookup by (class_id, spec_name).

Mirrors the pattern used by app.scoring.dungeons.registry. Specs whose
data hasn't been curated yet simply aren't in the lookup — the
/rotation endpoint falls back to the unclassified Phase 1 display in
that case.
"""
import importlib

from app.rotation.spec_data import SpecRotationData


# Module basenames under app.rotation.specs. Add a new spec by creating
# its file and appending the basename here. Order doesn't matter — the
# lookup is keyed by (class_id, spec_name) from the module's data.
ACTIVE_SPEC_MODULES: tuple[str, ...] = (
    "fury_warrior",
)


def _load_specs() -> dict[tuple[int, str], SpecRotationData]:
    specs: dict[tuple[int, str], SpecRotationData] = {}
    for module_name in ACTIVE_SPEC_MODULES:
        module = importlib.import_module(f"app.rotation.specs.{module_name}")
        data: SpecRotationData = module.SPEC
        specs[(data.class_id, data.spec_name)] = data
    return specs


_SPECS = _load_specs()


def get_spec_data(class_id: int, spec_name: str) -> SpecRotationData | None:
    """Return the curated data for (class_id, spec_name), or None when
    this spec hasn't been curated yet."""
    return _SPECS.get((class_id, spec_name))


def covered_specs() -> list[tuple[int, str]]:
    """List of (class_id, spec_name) pairs that have curated rotation
    data. Useful for an admin/status endpoint down the line."""
    return list(_SPECS.keys())
