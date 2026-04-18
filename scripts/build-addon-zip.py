"""Regenerate public addon zips from the repo addon folders.

Umbra/      -> frontend/public/Umbra.zip      (advertised download)
Umbra-dev/  -> frontend/public/Umbra-dev.zip  (direct URL only,
                                               not linked from the site)

Run whenever either addon folder changes, then commit the updated
zips alongside the Lua changes. The zip on the website only updates
when we push the corresponding folder.

Cross-platform: uses Python's zipfile + forward-slash arcnames so
macOS / Linux / Windows / 7-Zip all unzip cleanly into an addon
folder ready to drop into Interface/AddOns/.
"""
from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path


def build_zip(repo_root: Path, folder_name: str, zip_name: str) -> Path | None:
    src = repo_root / folder_name
    if not src.is_dir():
        print(f"  (skip) source missing: {src}")
        return None

    out = repo_root / "frontend" / "public" / zip_name
    out.parent.mkdir(parents=True, exist_ok=True)

    added = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(src):
            for f in files:
                # Skip packaging / tooling metadata — not runtime content.
                if f.startswith(".") or f == ".pkgmeta":
                    continue
                full = Path(root) / f
                # Arcname relative to repo root, posix form. Also normalize
                # the top-level folder to 'Umbra' so Umbra-dev.zip extracts
                # to an 'Umbra' folder — WoW loads addons by folder name,
                # and the folder name must match the .toc basename.
                rel_full = full.relative_to(repo_root).as_posix()
                rel = rel_full.replace(f"{folder_name}/", "Umbra/", 1)
                zf.write(full, rel)
                added += 1

    size_kb = out.stat().st_size / 1024
    print(f"  {zip_name}: {added} files, {size_kb:.1f} KB -> {out}")
    return out


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    print("Building addon zips...")
    build_zip(repo_root, "Umbra", "Umbra.zip")
    build_zip(repo_root, "Umbra-dev", "Umbra-dev.zip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
