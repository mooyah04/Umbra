"""Promote Umbra-dev/ -> Umbra/ after internal validation.

The public download at wowumbra.gg/Umbra.zip only updates when Umbra/
changes. Workflow:

  1. Make changes in Umbra-dev/. Rebuild Umbra-dev.zip via
     scripts/build-addon-zip.py. Test internally.
  2. Once validated, run this script. It mirrors Umbra-dev/ onto
     Umbra/ and rebuilds both zips.
  3. Commit + push — the public download now reflects the new
     changes.

This script never touches Umbra-dev/. If you want to discard a
staged change, edit or reset Umbra-dev/ directly.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    dev = repo_root / "Umbra-dev"
    live = repo_root / "Umbra"

    if not dev.is_dir():
        sys.exit(f"Umbra-dev/ not found at {dev}")

    # Quick visual diff preview so the operator can confirm what they're promoting.
    print(f"About to promote:  {dev}  ->  {live}")
    print("Current files in Umbra-dev/:")
    for f in sorted(p for p in dev.rglob("*") if p.is_file()):
        print(f"  {f.relative_to(dev)}")

    confirm = input("\nProceed? [y/N] ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        return 1

    # Mirror: remove the live folder contents and re-copy from dev.
    # Using shutil.copytree with dirs_exist_ok preserves file identity
    # for git so only actually-changed files show up in the diff.
    if live.exists():
        shutil.rmtree(live)
    shutil.copytree(dev, live)
    print(f"\nPromoted Umbra-dev/ -> Umbra/")

    # Rebuild both zips so frontend/public/Umbra.zip reflects the new
    # live state and frontend/public/Umbra-dev.zip stays current too.
    build = repo_root / "scripts" / "build-addon-zip.py"
    subprocess.run([sys.executable, str(build)], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
