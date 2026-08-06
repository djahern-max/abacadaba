# Deployment

abacadaba runs on DigitalOcean App Platform: one App with two components in
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

Domains: `abacadaba.com` → `web`, `api.abacadaba.com` → `api`. Both are on
the same registrable domain on purpose — see the cookie note in
`current-feature.md`. Certificates are issued and renewed automatically by
the platform once DNS points at it.

## Environment variables

### `api` and `migrate` (same env group — the migration job needs DB access,
nothing else)

| Var | Value | Source |
|---|---|---|
| `DATABASE_URL` | — | Injected automatically by the App Platform database binding. Do not paste a connection string by hand. |
| `CORS_ORIGINS` | `https://abacadaba.com` | Set manually, plain env var |
| `SPACES_KEY` | — | Encrypted secret, set manually in the App Platform console |
| `SPACES_SECRET` | — | Encrypted secret, set manually in the App Platform console |
| `SPACES_REGION` | `nyc3` | Plain env var (match wherever the Spaces bucket actually lives) |
| `SPACES_BUCKET` | `abacadaba` | Plain env var |
| `SPACES_ENDPOINT` | `https://nyc3.digitaloceanspaces.com` | Plain env var |
| `SITE_URL` | `https://abacadaba.com` | Plain env var |
| `SESSION_COOKIE_SECURE` | `true` | Plain env var |
| `SESSION_COOKIE_DOMAIN` | `.abacadaba.com` | Plain env var — leading dot so the cookie is sent to both hosts |
| `ENVIRONMENT` | `production` | Plain env var — disables `/docs` and `/redoc` |
| `PORT` | — | Injected automatically by App Platform |

Never put `SPACES_KEY` or `SPACES_SECRET` in a build arg — build args are
visible in build logs. They go in as encrypted (secret-type) env vars only.

### `web`

Vite bakes env vars into the JS bundle at build time, so these are not
App Platform runtime env vars — they come from `frontend/.env.production`,
which is committed to the repo (no secrets in it) and read automatically by
`npm run build`:

| Var | Value |
|---|---|
| `VITE_API_URL` | `https://api.abacadaba.com` |
| `VITE_SITE_URL` | `https://abacadaba.com` |

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

1. Create the App from this GitHub repo with the components above.
2. Attach the managed Postgres cluster via App Platform's database binding
   (not a pasted connection string).
3. Set the secrets and plain env vars listed above on `api` and `migrate`.
4. Point `abacadaba.com` and `api.abacadaba.com` at `web` and `api` and let
   the platform issue certificates.
5. Enable automatic deploys from `main`.
6. After the first successful deploy: run `scripts/seed.py` once, register
   an account through the live site, then run `scripts/make_admin.py` on
   that account through the Console.
7. Upload one real video to the production lesson via
   `backend/scripts/upload_video.py` (or the admin UI, once logged in as the
   new admin) so the deployed app has working content.
