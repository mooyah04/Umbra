"""Regenerate frontend/public/Umbra.zip from the Umbra/ addon folder.

Run whenever the addon files change, then commit the updated zip.
The public download on wowumbra.gg serves this file.

Cross-platform: uses Python's zipfile + forward-slash arcnames so
macOS / Linux / Windows / in-game 7-Zip all unzip cleanly into an
'Umbra/' folder ready to drop into Interface/AddOns/.
"""
from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path


def build(repo_root: Path) -> Path:
    src = repo_root / "Umbra"
    if not src.is_dir():
        sys.exit(f"Source addon folder missing: {src}")

    out = repo_root / "frontend" / "public" / "Umbra.zip"
    out.parent.mkdir(parents=True, exist_ok=True)

    added = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(src):
            for f in files:
                full = Path(root) / f
                # Arcname relative to repo root, posix form so every OS
                # can extract cleanly.
                rel = full.relative_to(repo_root).as_posix()
                zf.write(full, rel)
                print(f"  + {rel}")
                added += 1

    size_kb = out.stat().st_size / 1024
    print(f"\n{out.name}: {added} files, {size_kb:.1f} KB")
    return out


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    build(repo_root)
