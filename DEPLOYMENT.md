# Deployment

abacadaba runs on DigitalOcean App Platform: one App with three components in
front of a managed Postgres cluster. This doc is the runbook — how it's put
together, where every setting comes from, and how to do the things you'll
inevitably need to do again in six months and won't remember.

## App components

| Component | Type | Source dir | Notes |
|---|---|---|---|
| `api` | Service (Dockerfile) | `backend/` | Builds `backend/Dockerfile`, listens on `$PORT` (8080 default) |
| `web` | Static Site | `frontend/` | Build command `npm run build`, output dir `dist` |
| `migrate` | Pre-Deploy Job | `backend/` | Same Dockerfile/image as `api`, command `alembic upgrade head` |
| `abacadaba-db` | Managed Postgres | — | Attached via App Platform's database binding |

Domains: `abacadaba.com` → `web`, `api.abacadaba.com` → `api`. Certificates are
issued and renewed automatically by the platform once DNS points at it.

### Why both hosts share one registrable domain

This is deliberate and load-bearing, not an aesthetic choice. Because
`abacadaba.com` and `api.abacadaba.com` share a registrable domain, the session
cookie is same-site and `SameSite=Lax` works unchanged. If the API lived on a
different domain the cookie would need `SameSite=None; Secure`, and Safari's
tracking prevention would make sign-in unreliable in ways that are miserable to
diagnose.

`SESSION_COOKIE_DOMAIN` is set to `.abacadaba.com` in production — with the
leading dot — so the cookie is sent to both hosts. Locally it stays unset, so
the cookie is host-only. This comes from config, never a hardcoded string.

**Do not move the API to a different domain.**

## Environment variables

### `api` and `migrate`

Both components get the same set. The migration job needs database access and
nothing else, but keeping one env group avoids the failure mode where `api`
works and `migrate` silently can't reach Postgres.

| Var | Value | Source |
|---|---|---|
| `DATABASE_URL` | `${abacadaba-db.DATABASE_URL}` | Binding reference. You add the var yourself and set its value to that literal string — App Platform substitutes the real connection string at runtime. Never paste a connection string by hand. |
| `CORS_ORIGINS` | `https://abacadaba.com` | Plain env var. Comma-separated if you ever add more. See the `www` note below. |
| `SPACES_KEY` | — | Encrypted secret, set manually in the App Platform console |
| `SPACES_SECRET` | — | Encrypted secret, set manually in the App Platform console |
| `SPACES_REGION` | `nyc3` | Plain env var (match wherever the Spaces bucket actually lives) |
| `SPACES_BUCKET` | `abacadaba` | Plain env var |
| `SPACES_ENDPOINT` | `https://nyc3.digitaloceanspaces.com` | Plain env var |
| `SITE_URL` | `https://abacadaba.com` | Plain env var. Certificate verification URLs are built from this — if it's wrong, issued certificates point at the wrong host and there's no retroactive fix. |
| `SESSION_COOKIE_SECURE` | `true` | Plain env var |
| `SESSION_COOKIE_DOMAIN` | `.abacadaba.com` | Plain env var — leading dot so the cookie is sent to both hosts |
| `ENVIRONMENT` | `production` | Plain env var — disables `/docs` and `/redoc` |
| `PORT` | — | Injected automatically by App Platform |

Never put `SPACES_KEY` or `SPACES_SECRET` in a build arg — build args are
visible in build logs. They go in as encrypted (secret-type) env vars only.

#### A note on the DATABASE_URL scheme

The managed database binding hands out a URL beginning with `postgresql://`.
SQLAlchemy resolves that bare scheme to **psycopg2**, which this project does
not install — `requirements.txt` has `psycopg[binary]`, which is psycopg 3.
Left alone, both `api` and `migrate` crash on startup with
`ModuleNotFoundError: No module named 'psycopg2'`.

`app/config.py` therefore has a `field_validator` on `database_url` that
rewrites `postgresql://` to `postgresql+psycopg://`. It lives in config rather
than `db.py` because `alembic/env.py` reads `settings.database_url` directly and
never imports the engine — a fix in `db.py` alone would leave the migration job
broken, and a failing pre-deploy job aborts the entire deploy.

**Do not "simplify" that validator away.** It looks like a no-op locally,
because `.env` already spells the driver out.

#### The `www` decision

`CORS_ORIGINS` covers the apex domain only. If you point `www.abacadaba.com` at
the app as a second domain rather than configuring it as a redirect to the apex,
its requests will fail CORS. Prefer setting `www` up as a redirect in the
platform's domain settings and leaving `CORS_ORIGINS` alone.

### `web`

Vite bakes env vars into the JS bundle at build time, so these are not
App Platform runtime env vars — they come from `frontend/.env.production`,
which is committed to the repo (no secrets in it) and read automatically by
`npm run build`:

| Var | Value |
|---|---|
| `VITE_API_URL` | `https://api.abacadaba.com` |
| `VITE_SITE_URL` | `https://abacadaba.com` |

Changing either of these requires a rebuild, not just a restart.

## Health check

The `api` component's health check must be an **HTTP** check pointed at
`/api/v1/health`:

> App Platform console → `api` → Settings → Health Checks → HTTP Path
> `/api/v1/health`

App Platform's default is a TCP check on the service port. A TCP check passes as
long as uvicorn is listening — including when the database is unreachable, which
is the single most likely production failure and the exact case `/api/v1/health`
was written to catch. It runs `SELECT 1` and returns 503 when that fails.

## SPA rewrite

The `web` static site component has its **Catchall Document** setting (App
Platform console: component → Settings → Catchall Document, or
`catchall_document: index.html` in the app spec) set to `index.html`. Without
this, refreshing on a client-side route like `/lessons/intro-to-ratios`
returns a 404 instead of letting the React router handle it.

## Release / migrations

Migrations run as the `migrate` Pre-Deploy Job component, command
`alembic upgrade head`, using the same source and Dockerfile as `api`. App
Platform runs pre-deploy jobs to completion before routing traffic to the new
`api` version, and aborts the deploy if the job fails — so a bad migration
never leaves the app half-upgraded. This is why migrations are a separate
job and not something baked into the container's `CMD`: a crash-looping
container would otherwise retry the migration on every restart.

## Running a one-off command in production

Open the `api` component in the App Platform console → **Console** tab. This
opens a shell in a running instance of the deployed container. From there:

    python -m scripts.make_admin someone@example.com
    python -m scripts.seed

(`seed.py` only ever upserts, never deletes, so it's safe to re-run.)

Note the container has no video files in it, so this is *not* where video
uploads happen — see below.

## Uploading a video to production

`scripts/upload_video.py` runs **from your own machine**, not from the App
Platform console: the video file lives on your laptop, not inside the container.
It logs in as an admin over HTTPS and posts the file to the live API.

    cd backend && source .venv/bin/activate
    API_BASE_URL=https://api.abacadaba.com/api/v1 \
    ADMIN_EMAIL=you@example.com \
    ADMIN_PASSWORD='...' \
    python -m scripts.upload_video intro-to-ratios ./sample.mp4

| Var | Value | Notes |
|---|---|---|
| `API_BASE_URL` | `https://api.abacadaba.com/api/v1` | Defaults to `http://localhost:8000/api/v1` when unset. **Set it explicitly for production.** |
| `ADMIN_EMAIL` | — | An account that has already been promoted with `make_admin.py` |
| `ADMIN_PASSWORD` | — | That account's password. Don't commit it; it's in `.env.example` as a blank. |

Things that go wrong here:

- **A 401 on the upload after a successful login** means the session cookie
  wasn't sent back. The cookie is scoped to `.abacadaba.com`, so httpx's cookie
  jar only returns it when `API_BASE_URL` really is the `api.` host. Pointing at
  localhost fails this way silently rather than with a connection error.
- **`nodename nor servname provided`** is DNS, not the script — the domain
  isn't resolving yet.
- **A 413** is App Platform's ingress body limit, not application code. The
  answer is uploading to Spaces directly rather than through the API.

## Getting a shell on the database

1. DigitalOcean console → Databases → `abacadaba-db` → **Connection Details**.
2. If connecting from your own machine rather than from inside the app, add
   your current IP under **Trusted Sources** first — the cluster is not
   open to the public internet by default.
3. Copy the connection string (use the one with `sslmode=require`) and run:

       psql "<connection string>"

   `doctl databases connection abacadaba-db --format Host,Port,User,Password,Database,SSL`
   gets you the same values from the CLI if you have `doctl` set up locally.

The `api` and `migrate` components talk to the same cluster over the
private network via the injected `DATABASE_URL` — no trusted-source entry
needed for those.

## Promoting an admin

The account must already be registered (sign up normally through the site
first). Then, from the production console (see above):

    python -m scripts.make_admin someone@example.com

This flips `is_admin` on the existing user row. There is no way to create an
admin that hasn't registered first.

## First deploy checklist

1. Point `abacadaba.com`'s nameservers at DigitalOcean. Do this **first** —
   it's the only step with propagation delay, and certificates can't be issued
   until it resolves.
2. Create the App from this GitHub repo with the components above.
3. Attach the managed Postgres cluster via App Platform's database binding
   (not a pasted connection string).
4. Set the secrets and plain env vars listed above on `api` and `migrate`.
5. Set the `api` health check to HTTP `/api/v1/health` and the `web` catchall
   document to `index.html`. Neither is the platform default.
6. Point `abacadaba.com` and `api.abacadaba.com` at `web` and `api` and let
   the platform issue certificates.
7. Enable automatic deploys from `main`.
8. After the first successful deploy, from the Console: run
   `python -m scripts.seed` once.
9. Register an account through the live site, then promote it with
   `python -m scripts.make_admin` from the Console.
10. From your laptop, upload one real video with `scripts/upload_video.py` and
    `API_BASE_URL` pointed at production, so the deployed app has working
    content.

## Verifying the deploy

Feature 009 isn't done until all of these hold:

- [ ] `https://abacadaba.com` loads over TLS with a valid certificate
- [ ] the lesson list renders from the production database
- [ ] a video plays (proves Spaces credentials and presigned URLs work)
- [ ] refreshing on `/lessons/intro-to-ratios` does not 404
- [ ] registering works, and the session cookie shows `Secure`, `HttpOnly`,
      `SameSite=Lax`, domain `.abacadaba.com`
- [ ] signing out and back in works, proving the cookie survives both hosts
- [ ] a certificate's verification URL points at the real domain, not localhost
- [ ] `https://api.abacadaba.com/docs` returns 404
- [ ] pushing to `main` triggers a deploy that runs migrations first
