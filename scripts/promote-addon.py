"""Promote Umbra-dev/ -> Umbra/ after internal validation.

The public download at wowumbra.gg/Umbra.zip only updates when Umbra/
changes. Workflow:

  1. Make changes in Umbra-dev/. Rebuild Umbra-dev.zip via
     scripts/build-addon-zip.py. Test internally.
  2. Once validated, run this script. It mirrors Umbra-dev/ onto
     Umbra/ and rebuilds both zips.
  3. Commit + push — the public download now reflects the new
     changes.

Dev-only code blocks are stripped from the live mirror. Wrap any
debug-only code (e.g. /umbra empty preview toggle) in:

    -- @dev-only:begin
    ... code that should NOT ship to the public addon ...
    -- @dev-only:end

The script removes those lines (inclusive of the markers) when copying
.lua files into Umbra/. Markers are line-precise and only recognized on
their own line (leading whitespace ok). Nesting is not supported.

This script never touches Umbra-dev/. If you want to discard a
staged change, edit or reset Umbra-dev/ directly.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

# Match lines that are nothing but a dev-only marker (any indent).
_DEV_BEGIN_RE = re.compile(r"^\s*--\s*@dev-only:begin\s*$")
_DEV_END_RE   = re.compile(r"^\s*--\s*@dev-only:end\s*$")


def _strip_dev_only(text: str, file_label: str) -> tuple[str, int]:
    """Drop everything between @dev-only:begin and @dev-only:end (inclusive).
    Returns the stripped text plus the count of blocks removed. Bails
    loudly on mismatched markers — silent stripping bugs are nasty.
    """
    out_lines: list[str] = []
    in_block = False
    blocks = 0
    for ln, line in enumerate(text.splitlines(keepends=True), start=1):
        if _DEV_BEGIN_RE.match(line):
            if in_block:
                sys.exit(
                    f"{file_label}:{ln}: nested @dev-only:begin "
                    "(previous block never closed)"
                )
            in_block = True
            continue
        if _DEV_END_RE.match(line):
            if not in_block:
                sys.exit(
                    f"{file_label}:{ln}: @dev-only:end without a matching :begin"
                )
            in_block = False
            blocks += 1
            continue
        if not in_block:
            out_lines.append(line)
    if in_block:
        sys.exit(f"{file_label}: @dev-only:begin never closed")
    return "".join(out_lines), blocks


def _mirror_with_strip(src: Path, dst: Path) -> None:
    """shutil.copytree-equivalent that pipes every .lua file through
    _strip_dev_only. Non-Lua files (textures, .toc, .pkgmeta, README,
    CHANGELOG, etc.) are copied byte-for-byte.
    """
    for src_file in src.rglob("*"):
        rel = src_file.relative_to(src)
        dst_file = dst / rel
        if src_file.is_dir():
            dst_file.mkdir(parents=True, exist_ok=True)
            continue
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        if src_file.suffix.lower() == ".lua":
            text = src_file.read_text(encoding="utf-8")
            stripped, blocks = _strip_dev_only(text, str(rel))
            dst_file.write_text(stripped, encoding="utf-8", newline="")
            if blocks:
                print(f"  stripped {blocks} dev-only block(s) from {rel}")
        else:
            shutil.copy2(src_file, dst_file)


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

    # Mirror: remove the live folder contents and re-copy from dev,
    # piping .lua files through _strip_dev_only so debug-only blocks
    # never reach the public addon.
    if live.exists():
        shutil.rmtree(live)
    live.mkdir(parents=True, exist_ok=True)
    _mirror_with_strip(dev, live)
    print(f"\nPromoted Umbra-dev/ -> Umbra/")

    # Rebuild both zips so frontend/public/Umbra.zip reflects the new
    # live state and frontend/public/Umbra-dev.zip stays current too.
    build = repo_root / "scripts" / "build-addon-zip.py"
    subprocess.run([sys.executable, str(build)], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
