# Submission runbook (CurseForge + Wago)

Step-by-step for actually submitting Umbra. Follow top to bottom. You
should be able to sit down and do this in one session without looking
anything else up.

## 0. Pre-flight

Already done, but sanity-check before you start:

- `Umbra/Umbra.toc` has `## Version: 0.3.3`
- `Umbra/CHANGELOG.md` has a `[0.3.3]` entry
- `LICENSE` exists at repo root (MIT)
- `frontend/public/Umbra.zip` is the latest build
- Screenshots live at `docs/listings/screenshots/01-04.png` (and `05` bonus)

If any of those are stale, run `python scripts/promote-addon.py` to
rebuild zips from `Umbra-dev/`.

## 1. Tag the release

```bash
git tag v0.3.3
git push --tags
```

CurseForge doesn't require a git tag, but it's the right artifact to
point at when someone asks "where did this zip come from."

## 2. CurseForge

### 2a. Account

1. Create a CurseForge/Overwolf account at <https://www.curseforge.com>.
   Use `logankessinger25@gmail.com`.
2. Verify the email.
3. Go to Author Portal at <https://authors.curseforge.com>. Sign in.

### 2b. Create the project

1. In Author Portal, click **Create Project** → **World of Warcraft**.
2. Fill the create form:
   - **Project name:** `Umbra`
   - **Slug:** `umbra` (if taken, fall back to `wowumbra-gg`)
   - **Category:** `Addons > Plugins > Combat > Mythic Plus`.
     Secondary if it offers: `Tooltips`.
   - **Summary (card blurb):**
     `Mythic+ performance grades on tooltips and the Group Finder. Backed by Warcraft Logs data. No network calls from the addon.`
   - **Description:** paste the fenced `markdown` block from
     `docs/listings/curseforge.md` (everything between the triple
     backticks under *Long description*). CurseForge renders markdown.
   - **License:** MIT.
   - **Homepage / website:** `https://wowumbra.gg`
   - **Source URL:** `https://github.com/mooyah04/Umbra`

3. **Submit project.** CurseForge holds new projects for approval.
   Usually 24-72 hours.

### 2c. Upload files + assets (can do while project is pending)

1. **Icon.** Upload `docs/listings/icon.png` (1024x1024 dark-bg
   stylized U) as the project icon. CurseForge auto-downsamples.

2. **Screenshots.** In the project's *Images* tab, upload in order:
   - `screenshots/01-panel.png`
   - `screenshots/02-lfg-applicant-tooltip.png`
   - `screenshots/03-lfg-group-tooltip.png`
   - `screenshots/04-world-tooltip.png`
   - (Optional bonus) `screenshots/05-profile-popup.png`

   Caption them so the first-card preview makes sense:
   - 01: "Your Umbra stats panel"
   - 02: "Grades on LFG applicants"
   - 03: "Grades on group listings"
   - 04: "Grades on world player tooltips"
   - 05: "Open your full profile on wowumbra.gg"

3. **Tags.** Paste these into the project's tag field:
   ```
   mythic-plus, m+, tooltip, group-finder, lfg, raider.io-alternative,
   performance, grading, warcraftlogs, wcl
   ```

4. **Upload the zip file.**
   - Go to the *Files* tab → *Upload File*.
   - Upload `frontend/public/Umbra.zip`.
   - **Release type:** Release (not Alpha/Beta).
   - **Display name:** `0.3.3`.
   - **Game version:** tick all boxes for *The War Within* /
     Interface 12.0.01.
   - **Changelog field:** copy the `[0.3.3]` section from
     `Umbra/CHANGELOG.md`.
   - Publish.

### 2d. After CurseForge approves

1. Copy the project's numeric ID from the Author Portal URL
   (e.g., `authors.curseforge.com/projects/123456`).
2. Update `Umbra/Umbra.toc`:
   ```
   ## X-Curse-Project-ID: 123456
   ```
3. Also update `Umbra-dev/Umbra.toc` the same way (keeps them in
   sync per the two-track convention).
4. Commit + push:
   ```bash
   git add Umbra/Umbra.toc Umbra-dev/Umbra.toc
   git commit -m "Addon: wire Curse-Project-ID after CF approval"
   git push
   ```

## 3. Wago

### 3a. Account

1. Create a Wago account at <https://addons.wago.io>.
2. Verify email.

### 3b. Create the project

1. New Addon → WoW (Retail).
2. Fields:
   - **Name:** `Umbra`
   - **Category:** `Mythic+ Tools` (closest fit)
   - **License:** MIT
   - **Tagline:** paste from `wago.md` → `Tagline`.
   - **Description:** paste the fenced `markdown` block from
     `wago.md` → *Description*.
   - **Tags:** paste from `wago.md`.

3. Upload the same icon + the 4 screenshots.

4. Upload the zip in *Files* → release type `Stable`, version `0.3.3`,
   paste the 0.3.3 changelog section.

5. Submit.

### 3c. After Wago assigns an ID

1. Copy the project's alphanumeric slug/ID from the Wago URL.
2. Update both `Umbra/Umbra.toc` and `Umbra-dev/Umbra.toc`:
   ```
   ## X-Wago-ID: <id>
   ```
3. Commit + push alongside (or bundled with) the CurseForge commit.

## 4. Site changelog entry

After both listings are live, add a site-facing changelog entry in
`frontend/src/lib/changelog.ts`:

```ts
{
  date: "<today's ISO date>",
  title: "Umbra is on CurseForge and Wago",
  category: "new",
  body:
    "You can now install Umbra from CurseForge and Wago, and it'll auto-update from your addon manager. Direct-download from wowumbra.gg still works too, whichever you prefer.",
},
```

## 5. README.md badges (optional polish)

Once IDs exist, add CurseForge + Wago badges to `README.md` so the
GitHub landing page looks populated.

```md
[![CurseForge](https://img.shields.io/curseforge/dt/<id>?label=CurseForge)](https://www.curseforge.com/wow/addons/umbra)
[![Wago](https://img.shields.io/badge/Wago-download-blue)](https://addons.wago.io/addons/<slug>)
```

## Troubleshooting

**CurseForge rejected for "project name already exists."** Try `umbra`,
`wowumbra`, `wowumbra-gg`, `umbra-grades`. Slug is independent of
display name so you can still call it "Umbra" in the UI.

**CurseForge asks for mandatory dependencies.** We have none.

**Zip is rejected for "folder name mismatch."** The top-level folder
inside `Umbra.zip` must be `Umbra` (matches the `.toc` basename). The
build script enforces this; if it breaks, rebuild with
`python scripts/build-addon-zip.py`.

**Wago tagline cap.** If Wago caps the tagline below our 70-char line,
trim to: `M+ performance grades on tooltips and in the LFG.`
