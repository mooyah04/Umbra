# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Umbra is a World of Warcraft addon (Interface 120000 / The War Within) that displays performance grades on player tooltips. When you hover over a player, the tooltip shows their "Deep Audit" grade (S+ through F-), rotational parity (DPS performance %), and utility/kick count from the `Umbra_Database` saved variable.

## Architecture

- **Umbra.toc** — Addon manifest. Declares metadata, saved variables (`Umbra_Database`), and load order.
- **UmbraData.lua** — Loaded first. Initializes `Umbra_Database` with player lookup data keyed by `"Name-Realm"` format.
- **Core.lua** — Loaded second. Hooks `GameTooltip` via `OnTooltipSetUnit` to inject Umbra audit lines when hovering over players.

The addon uses WoW's SavedVariables system — `Umbra_Database` persists across sessions and is the single data source for all tooltip lookups. Player keys use the format `"Name-Realm"` with spaces stripped from realm names.

## Backend (`backend/`)

Python 3.11+ / FastAPI service that powers the scoring pipeline:

- **`app/wcl/`** — Warcraft Logs API v2 client (OAuth2 + GraphQL). Fetches M+ encounter rankings.
- **`app/scoring/engine.py`** — Role-aware grading engine. Scores DPS, healers, and tanks on different weighted axes (see role weights in file). Outputs composite 0-100 → letter grade (S+ to F-).
- **`app/scoring/roles.py`** — Maps all 39 WoW specs (class_id + spec_name) to tank/healer/dps.
- **`app/pipeline/ingest.py`** — Orchestrates fetch → score → store. Supports single player and batch with rate-limited concurrency.
- **`app/export/lua_writer.py`** — Generates `UmbraData.lua` from DB. Exports role-specific category breakdowns.
- **`app/models.py`** — SQLAlchemy models: `Player`, `DungeonRun`, `PlayerScore`. Scores are per-player-per-role.

### Backend Commands

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env                          # Fill in WCL_CLIENT_ID, WCL_CLIENT_SECRET, DATABASE_URL
uvicorn app.main:app --reload                 # Start dev server (auto-creates tables)
alembic revision --autogenerate -m "message"  # Create migration
alembic upgrade head                          # Run migrations
```

### API Endpoints

- `GET /api/player/{region}/{realm}/{name}` — Player score (triggers WCL ingest if uncached)
- `POST /api/ingest` — Bulk ingest `{"players": [{"name", "realm", "region"}, ...]}`
- `GET /api/export/lua` — Download generated `UmbraData.lua`

## Addon Development Notes

- No build system — files are plain Lua loaded directly by the WoW client.
- To test, copy/symlink the `Umbra` folder into `World of Warcraft/_retail_/Interface/AddOns/` and `/reload` in-game.
- The `.toc` file's `## Interface:` value must match the current WoW client version to load without "out of date" being checked.
- Load order matters: `UmbraData.lua` must come before `Core.lua` in the `.toc` file since Core references `Umbra_Database`.
