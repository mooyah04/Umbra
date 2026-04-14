# Railway + Vercel deployment guide

This walks you through deploying Umbra to live URLs so you can share work-in-progress builds with friends. **Total time: ~60–90 minutes** for the first deploy, ~0 minutes for each subsequent push (automatic).

**Architecture:**

```
Browser
   │
   │  https://wowumbra.gg (or umbra-xxx.vercel.app)
   ▼
┌─────────────────┐     https://api.wowumbra.gg     ┌──────────────────┐     ┌────────────┐
│  Vercel         │ ────────────────────────────▶│  Railway         │────▶│  Postgres  │
│  (Next.js       │     REST API calls           │  (FastAPI in     │     │  (Railway  │
│   frontend)     │                              │   Docker)        │     │   plugin)  │
└─────────────────┘                              └──────────────────┘     └────────────┘
     deploys on                                       deploys on
     every push                                       every push
```

Both services auto-deploy on every push to GitHub.

---

## 0. Prerequisites

- [x] GitHub repo: `https://github.com/mooyah04/Umbra.git`
- [ ] GitHub account logged in (used to sign into both platforms)
- [ ] A WCL API client (https://www.warcraftlogs.com/api/clients) — you already have `WCL_CLIENT_ID` and `WCL_CLIENT_SECRET`
- [ ] Payment method on Railway (~$5 hobby plan; free trial credit covers the first few days)
- [ ] **Local checklist:** all current work committed + pushed to `master`. Railway pulls from GitHub — if it's not on the remote, it doesn't deploy.

Generate a fresh API key locally and keep it handy:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
You'll paste this into Railway's env vars as `API_KEY`.

---

## 1. Deploy the backend to Railway

### 1a. Create project

1. Go to https://railway.app → sign in with GitHub
2. **New Project** → **Deploy from GitHub repo** → select `mooyah04/Umbra`
3. Railway scans the repo and finds `backend/Dockerfile` — confirm.
4. Set the service's **Root Directory** to `backend` (Settings → Root Directory). Railway will only build from that folder.

### 1b. Add Postgres

1. In the project view, click **+ New** → **Database** → **Add PostgreSQL**
2. Railway provisions a Postgres instance and auto-injects a `DATABASE_URL` env var into the backend service. Our app reads this directly.
3. **Important:** Railway's injected `DATABASE_URL` looks like `postgresql://user:pass@host:port/db`. Our SQLAlchemy config expects `postgresql+psycopg://...`. Override it in the backend's Variables tab:
   ```
   DATABASE_URL = postgresql+psycopg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}
   ```
   (Railway's variable reference syntax lets you compose it from the Postgres plugin's vars.)

### 1c. Set environment variables

In the backend service's **Variables** tab, add:

| Variable | Value |
|---|---|
| `WCL_CLIENT_ID` | your WCL client ID |
| `WCL_CLIENT_SECRET` | your WCL client secret |
| `WCL_MPLUS_ZONE_ID` | `47` (Midnight S1) |
| `API_KEY` | the token you generated above |
| `RATE_LIMIT_PUBLIC` | `60/minute` |
| `RATE_LIMIT_PLAYER_LOOKUP` | `20/minute` |
| `PORT` | `8000` (Railway auto-assigns but our Dockerfile exposes 8000) |

### 1d. Deploy

Railway should have started building automatically when you connected the repo. Watch the **Deployments** tab:

1. Build takes ~2-3 min (Docker image build + dependency install)
2. On success, check **Deployments** → **View Logs**. You should see:
   ```
   Running alembic upgrade head...
   INFO  [alembic.runtime.migration] Running upgrade -> a1b2c3d4e5f6, add enrichment fields
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```
3. Railway assigns a URL like `umbra-backend-production.up.railway.app`. Click **Settings** → **Generate Domain** if there isn't one yet.

### 1e. Smoke test

```bash
curl https://<your-railway-url>/api/health
# {"status":"ok","service":"umbra-score-engine"}
```

Try an admin-gated endpoint:
```bash
curl -H "X-API-Key: <your-key>" -X POST \
  -H "Content-Type: application/json" \
  -d '{"players":[{"name":"Mooyuh","realm":"Tarren Mill","region":"EU"}]}' \
  https://<your-railway-url>/api/ingest
```

If that returns a JSON response (even a failure) the stack is reachable.

---

## 2. Deploy the frontend to Vercel

### 2a. Create project

1. Go to https://vercel.com → sign in with GitHub
2. **Add New** → **Project** → **Import Git Repository** → select `mooyah04/Umbra`
3. **Framework Preset** should auto-detect as **Next.js**
4. **Root Directory** → set to `frontend`
5. Leave build settings at defaults (`next build`, output `.next`)

### 2b. Set environment variables

Under **Environment Variables**, add:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://<your-railway-url>` (no trailing slash) |

Any env var prefixed `NEXT_PUBLIC_` is exposed to the browser — appropriate here since the URL isn't secret.

### 2c. Deploy

Click **Deploy**. Vercel builds in ~60–90s and gives you a URL like `umbra-mooyah04.vercel.app`.

### 2d. Smoke test

Open the URL in a browser. You should see the home page render. Every subsequent push to `master` rebuilds automatically; pushes to feature branches get their own preview URL at `umbra-git-<branch>-mooyah04.vercel.app`.

---

## 3. Wire up CORS (one-time)

The backend's CORS allowlist is in `backend/app/main.py`:

```python
allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://wowumbra.gg",
    "https://www.wowumbra.gg",
],
```

Add your Vercel domain (and any preview domain pattern you want to allow) here, then commit + push:

```python
allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://wowumbra.gg",
    "https://www.wowumbra.gg",
    "https://umbra-mooyah04.vercel.app",         # production Vercel URL
    # For preview deploys, use allow_origin_regex instead — see below
],
```

For Vercel preview URLs (each branch gets a unique one), use a regex:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://umbra-[a-z0-9-]+-mooyah04\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 4. Custom domain (optional, when you're ready to share publicly)

### 4a. Frontend (`wowumbra.gg` → Vercel)

1. Vercel → your project → **Settings** → **Domains** → **Add** → enter `wowumbra.gg` and `www.wowumbra.gg`
2. Vercel shows DNS records to configure at your registrar:
   - `A` record → Vercel's IP
   - `CNAME` record for `www` → `cname.vercel-dns.com`
3. Wait 5-30 min for DNS propagation. Vercel auto-provisions TLS.

### 4b. Backend (`api.wowumbra.gg` → Railway)

1. Railway → backend service → **Settings** → **Networking** → **Custom Domain** → enter `api.wowumbra.gg`
2. Railway gives you a CNAME target (e.g., `xxx.up.railway.app`)
3. At your DNS registrar, add `CNAME api → <railway-target>`
4. Wait for propagation. Railway auto-provisions TLS.

### 4c. Update frontend env var

In Vercel, change `NEXT_PUBLIC_API_URL` from the Railway default URL to `https://api.wowumbra.gg`. Redeploy.

### 4d. Update CORS

Add `https://wowumbra.gg` and `https://www.wowumbra.gg` to the backend's allow_origins (already there in the default list).

---

## 5. Seed the database (first real data)

Your production DB starts empty. Kick off an initial crawl:

**Option A — via the `/api/ingest` endpoint** (from your local machine):
```bash
curl -H "X-API-Key: <your-key>" -X POST \
  -H "Content-Type: application/json" \
  -d '{"players":[
        {"name":"Mooyuh","realm":"Tarren Mill","region":"EU"},
        {"name":"SomeTopPlayer","realm":"Illidan","region":"US"}
      ]}' \
  https://<backend-url>/api/ingest
```

**Option B — run the crawler CLI in a Railway shell** (bigger seeding):
1. Railway → backend service → **Settings** → **Shell** (or use `railway run`)
2. Inside the container:
   ```bash
   python -m app.crawler.cli --seed "Mooyuh/tarren-mill/eu" --max-players 100 --depth 2
   ```

---

## 6. Sharing the preview with friends

Once `main` is deployed:
- **Production URL:** `https://umbra-mooyah04.vercel.app` (or `https://wowumbra.gg` with custom domain)
- **Per-branch URLs:** push any branch → Vercel generates `https://umbra-git-<branch>-mooyah04.vercel.app` within 90 seconds

Send friends the URL; they don't need accounts or credentials.

---

## 7. Day-to-day workflow

| Action | What happens |
|---|---|
| `git push` to master | Railway rebuilds backend + Vercel rebuilds frontend (~2 min total); prod URLs update |
| `git push feature/foo` | Vercel generates a preview URL; Railway stays on main unless you configure a staging service |
| Push a migration | Railway's entrypoint runs `alembic upgrade head` before starting the server |
| Env var change | Railway/Vercel → Variables → edit → **Redeploy** (env changes don't auto-trigger deploys) |

---

## 8. Cost tracking

- **Vercel Hobby:** free forever unless you hit 100GB bandwidth/month or 1M function invocations. Unlikely in friends-only preview phase.
- **Railway:** $5/mo hobby plan includes $5 of usage. Small always-on FastAPI + Postgres usually fits. Monitor in the project dashboard → **Metrics**.
- **DNS (wowumbra.gg):** whatever your registrar charges (usually $10–20/year).

Total for preview phase: **$5–10/month**.

---

## 9. Troubleshooting

**Build fails on Railway with `libpq` error:**
- Confirm the Dockerfile installs `libpq5`. It does — this is in `backend/Dockerfile`.

**Backend starts but every DB call 500s:**
- `DATABASE_URL` likely uses `postgresql://` (psycopg2-compatible) instead of `postgresql+psycopg://` (psycopg3). Check the Variables tab in Railway and use the composed form from step 1b.

**Frontend loads but API calls all fail with CORS errors:**
- Add the Vercel domain to `allow_origins` in `backend/app/main.py`, commit, push.

**Vercel preview says "Environment variable missing":**
- `NEXT_PUBLIC_API_URL` wasn't set for **Preview** environments. Re-add it and select all three (Production/Preview/Development).

**Alembic migration fails on first deploy:**
- Railway's Postgres plugin creates an empty database. Our migration `001_add_enrichment_fields_to_dungeon_runs.py` runs, but it depends on the initial schema from `Base.metadata.create_all()`. If it errors, temporarily set `RUN_MIGRATIONS=0`, let the app start (which auto-creates tables), then set it back and redeploy.

**Can't reach backend from browser (ERR_CONNECTION_REFUSED):**
- Check Railway → Settings → Networking: port must be set to `8000` (matching our Dockerfile).

---

## 10. What NOT to do in production (yet)

Current backend state is preview-safe but has known gaps before a wider launch:
- No frontend rate limiting (backend has it, but frontend could use it for spam protection)
- CORS is permissive (`allow_methods=["*"]`, `allow_headers=["*"]`) — fine for preview, tighten later
- No logging/monitoring pipeline — rely on Railway's built-in logs for now
- Postgres is a single instance with no automated backups configured — enable daily backups in Railway's Postgres settings before you have data you care about
- `/api/export/lua` has no caching — for a real WoW addon, put Cloudflare in front

These are all "post-friends-preview" concerns.
