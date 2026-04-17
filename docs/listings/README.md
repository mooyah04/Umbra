# Addon listing prep (CurseForge + Wago)

Prep material for the public launch on CurseForge and Wago. Nothing
here is published yet. **Hold on actually submitting until the RPGLogs
outreach reply lands** (see `memory/project_rpglogs_outreach.md`).

## Status

| Item | Owner | Status |
|---|---|---|
| Short description | me | done (`curseforge.md`) |
| Long description | me | done (`curseforge.md`) |
| Wago listing copy | me | done (`wago.md`) |
| `.toc` metadata (Version / X-Website / X-License / IconTexture) | me | done (in repo) |
| `## Version:` bump to 0.3.1 | me | done |
| Updated CHANGELOG.md | me | done |
| README points to Archon | me | done |
| **Screenshots (see shot-list below)** | Logan | todo |
| Project icon (256x256 PNG) | Logan | done — `icon.png` (1024x1024, stylized U with purple lightning / energy core on dark) |
| License file at repo root (MIT) | me | todo when pushing |
| CurseForge account + Curse-Project-ID | Logan | todo (blocked on submission) |
| Wago account + Wago-ID | Logan | todo (blocked on submission) |
| RPGLogs reply received | Logan | **BLOCKING — email sent 2026-04-17** |
| Actual submission | Logan | blocked on above |

## Screenshot shot-list

CurseForge wants 1-5 images, ideally 1920x1080 or 2560x1440, JPG/PNG.
Wago is similar. Aim for 4 good shots that tell the story.

### Required (these 4 are the main pitch)

1. **`/umbra` panel with your own graded character.**
   - Your own character ideally, so the card is fully populated
     (3D model, spec, ilvl, grade).
   - Panel centered, entire panel in frame, no UI bars behind it if
     possible.
   - `/reload` right before so the panel is fresh.

2. **Tooltip on an LFG applicant showing the grade.**
   - Open Group Finder → Mythic+ → pick any active listing → hover
     one of the applicants in the list. Screenshot with the tooltip
     visible.
   - Make sure the applicant has a grade (ideally not N/R). If they
     don't, wait for one who does.

3. **Group Finder list with inline grade badges.**
   - Full-width Group Finder list view. The "Umbra: B+" style badges
     should be visible on at least 2-3 applicants.
   - Best if some different grade colors are visible (e.g. one A,
     one B, one C).

4. **World tooltip hover on a player.**
   - Stand in a capital city. Hover a random high-level player.
   - Tooltip should show: "WoWUmbra.gg: <Grade> <Role>".

### Nice-to-have (one or both, if easy)

5. Minimap button visible on the minimap edge (mousing over it so
   the tooltip fires).
6. A side-by-side of two different grades on `/umbra` (e.g. your
   main showing S vs an alt showing C). Optional — skip if hassle.

### Screenshot tips

- Dark panel + transparent gradient backgrounds read better on
  CurseForge's white theme than on Wago's dark theme. Both should
  be fine, but if one shot looks muddy, try a less-busy game
  background.
- Hide your UI chrome where possible (alt+z on most setups toggles
  Blizzard's default UI bars).
- Use in-game settings to crank graphics to ultra for the screenshot
  session. The 3D model in the panel will look better.

## Listing copy

- `curseforge.md` — short desc + long desc, markdown-formatted.
- `wago.md` — Wago's preferred format with their field structure.

Both pull from the same feature list but phrase it for each audience.

## Icon

`icon.png` in this folder. 1024x1024 (CurseForge auto-scales to its
256x256 display slot, auto-downscales for card view at ~64x64). Stylized
"U" in the site's purple with a lightning / energy-core effect on a
dark backdrop. Centered composition reads well even at the smallest
card sizes. Upload as the project icon during submission.

In-game the addon still uses Blizzard's
`Interface\Icons\spell_shadow_twilight` — that's fine for the minimap
button and panel header, they have to be Blizzard-atlas paths.

## Submission checklist (when RPGLogs greenlights)

Run these in order:

1. Create LICENSE file (MIT) at repo root. Commit + push.
2. Tag the commit: `git tag v0.3.1 && git push --tags`.
3. Build the release zip: `python scripts/build-addon-zip.py`.
4. CurseForge: create project, upload zip, paste `curseforge.md` into
   the description field. Paste short description into the card
   blurb. Upload 4 screenshots + icon. Submit for approval.
5. Wago: same flow, paste `wago.md` content into the description
   field.
6. Once both are approved, paste the resulting IDs into the `.toc`:
   - `## X-Curse-Project-ID: <numeric id>`
   - `## X-Wago-ID: <alphanumeric id>`
   Commit + push.
7. Add a changelog entry for site users.
