# Current Feature

## Feature 009, Deploy to production

## Goal
abacadaba runs on the public internet at a real domain with TLS, a Postgres
database, and a repeatable deploy from main. Everything that works locally
works there, including session cookies and video playback.

## Architecture decision, revised
This feature was originally specced for DigitalOcean App Platform. It was
deployed instead to a **DigitalOcean Droplet** running Ubuntu 24.04, with
Docker Compose, nginx as reverse proxy, and Postgres in a container.

Reasons, recorded so the choice is legible later:
- Prior experience with raw VMs; deliberately continuing to build those skills.
- Cheaper: one $18/mo Droplet against roughly $25/mo of App Platform
  components plus a managed database.
- The tradeoff accepted in exchange: backups, deploys, TLS renewal, and OS
  patching are all owned here rather than by a platform.

The container image is unchanged, so this is reversible. `backend/Dockerfile`
would run on App Platform, Fly, or Cloud Run without modification.

## In scope
- Backend containerized and running on the Droplet under Docker Compose
- Frontend built off-box and served as static files by nginx
- Postgres in a container, with migrations run as a discrete step before the
  API restarts
- Production environment configuration, including secure cookies
- Domain and TLS for abacadaba.com and api.abacadaba.com
- Host hardening: SSH, ufw, DigitalOcean Cloud Firewall, container containment
- A production seed run, and the first admin account

## Out of scope
- CDN tuning, video transcoding, adaptive streaming
- Staging environments, blue green deploys, rollback automation
- Monitoring and alerting beyond the health endpoint (feature 013)
- Automated backups and restore testing (feature 013)
- Lesson thumbnails or images. Not specced in any feature yet; needs its own.

## The decision that prevents a day of cookie debugging
Put the API on api.abacadaba.com and the frontend on abacadaba.com. These share
a registrable domain, so the session cookie is same site and SameSite=Lax works
unchanged. If the API lived on a different domain the cookie would need
SameSite=None with Secure, and Safari's tracking prevention would make it
unreliable. Do not put them on different domains.

Set the cookie domain to .abacadaba.com in production so it is sent to both
hosts. Locally it stays host only. This comes from config, not a hardcoded
string.

## The decision that prevents a repeat compromise
An earlier project on a Droplet was most likely compromised through a corrupt
npm package. A malicious postinstall script executes at install time, as
whoever ran npm install, on whatever machine ran it. No firewall prevents this.

Therefore: **the Droplet never runs npm.** Node is not installed on it. The
frontend is built on the developer's machine or in CI, and only the resulting
`dist/` directory is shipped. Static HTML, CSS, and JS have no lifecycle hooks.

Do not add a frontend build step to the server. Do not add a Node container.

## Backend tasks — complete
1. `backend/Dockerfile`: python:3.12-slim, non-root `appuser`, `$PORT`-aware,
   single stage.
2. `backend/.dockerignore` excluding `.venv`, `__pycache__`, `tests`, `.env*`.
3. `app/config.py`: `SESSION_COOKIE_DOMAIN`, `ENVIRONMENT` defaulting to
   `development`, plus `SESSION_COOKIE_SECURE`, `SITE_URL`, `CORS_ORIGINS`.
4. Cookie code reads domain and secure from settings. SameSite is Lax.
5. `app/main.py`: `docs_url=None` and `redoc_url=None` when
   `ENVIRONMENT=production`. Verified returning 404 in production.
6. **`app/config.py` normalizes the DATABASE_URL scheme.** A bare
   `postgresql://` resolves to psycopg2, which is not installed; a
   `field_validator` rewrites it to `postgresql+psycopg://`. This lives in
   config rather than `db.py` because `alembic/env.py` reads
   `settings.database_url` directly and never imports the engine. Do not
   remove it — it is a no-op locally, which makes it look deletable.
7. `/api/v1/health` executes SELECT 1 and returns 503 when the database is
   unreachable.
8. `backend/scripts/seed.py` reconfirmed upsert-only, never deletes.
9. **`backend/scripts/upload_video.py` reads `API_BASE_URL` from the
   environment**, defaulting to localhost. It runs from the developer's
   machine against the production API, not on the server — the video file is
   local.

## Frontend tasks — complete
1. `frontend/.env.production` with `VITE_API_URL=https://api.abacadaba.com`
   and `VITE_SITE_URL=https://abacadaba.com`.
2. Deep links are handled by nginx `try_files $uri $uri/ /index.html;` in the
   apex server block. This replaces App Platform's Catchall Document setting.
3. `npm run build` succeeds with no warnings. Built off-box; only `dist/` is
   shipped.

## Deployment tasks — complete
1. Droplet: Ubuntu 24.04, 2 vCPU / 2 GB / 60 GB, 2 GB swap, `vm.swappiness=10`.
2. SSH hardened via `/etc/ssh/sshd_config.d/10-hardening.conf`: key-only, no
   root login, `AllowUsers deploy`. The drop-in takes precedence over
   cloud-init's `50-` file and survives package upgrades.
3. ufw: default deny inbound, `limit` on 22, allow 80 and 443. DigitalOcean
   Cloud Firewall applied with the same three ports — it filters at the network
   edge, which Docker cannot bypass.
4. Docker CE and Compose V2 from Docker's own apt repository.
5. `docker-compose.prod.yml` at the repo root:
   - `db` publishes **no ports**; the api reaches it as `db:5432`
   - `api` binds `127.0.0.1:8080` only
   - two networks: `backend` is `internal: true`, so the database container has
     no route to the internet; `api` also joins `egress` to reach Spaces
   - containment: `no-new-privileges`, `cap_drop: ALL` on api, `read_only`
     with a noexec `/tmp` tmpfs, cpu/memory/pids limits, log rotation
   - `FORWARDED_ALLOW_IPS` set so uvicorn honours nginx's `X-Forwarded-For`;
     without it every request appears to come from the Docker bridge gateway,
     which would silently defeat feature 013's per-IP rate limiting
6. nginx: apex serves `/var/www/abacadaba` with the SPA catchall, `www`
   301s to apex, `api.` reverse proxies to `127.0.0.1:8080` with
   `client_max_body_size 512M` for video uploads. Note nginx 1.24 needs
   `listen 443 ssl http2;` — the `http2 on;` directive is 1.25.1+.
7. TLS via certbot webroot for all three hostnames in one certificate, with a
   `--deploy-hook` reloading nginx on renewal. Renewal timer verified with
   `certbot renew --dry-run`.
8. Deploy order, which the platform used to own: pull, build, run
   `alembic upgrade head` in a one-off container, **then** restart the api. A
   failed migration must stop the deploy rather than leave the api serving
   against a schema it does not match.
9. Seed run, first admin promoted with `scripts/make_admin.py`, one real video
   uploaded to the production lesson.

## Remaining
- [x] `deploy.sh` at the repo root encoding the ordering in task 8, so
      redeploying is one command rather than remembered steps.
- [x] Rewrite `DEPLOYMENT.md` for this architecture. It currently describes
      App Platform components, env var bindings, and a Catchall Document
      setting that no longer exist.

## Write it down
`DEPLOYMENT.md` at the repo root records: the Droplet layout and where each
piece lives, every environment variable and where its value comes from, the
nginx SPA rewrite, how to run a one-off command in production, how to get a
psql shell, how to promote an admin, and how to deploy a change.

`HARDENING.md` records the security posture and the reasoning behind each
control, ordered by how much risk each one actually removes.

## Acceptance criteria
- [x] https://abacadaba.com loads over TLS with a valid certificate
- [x] the lesson list renders from the production database
- [x] a video plays, proving Spaces credentials and presigned URLs work
- [x] the unsigned Spaces URL returns 403, proving the Space is still private
- [x] refreshing on a deep link like /lessons/intro-to-ratios does not 404
- [x] registering an account on production works
- [x] the session cookie has Secure, HttpOnly, SameSite=Lax, and the
      .abacadaba.com domain
- [x] signing out and back in works, proving the cookie survives both hosts
- [x] completing a quiz produces a certificate whose verification URL points at
      the real domain, not localhost
- [x] https://api.abacadaba.com/docs returns 404 in production
- [x] only ports 22, 80, and 443 are reachable from the internet; 5432 and
      8080 are not
- [x] a deploy runs migrations before the api restarts
- [x] DEPLOYMENT.md exists and is accurate

## When done
Append an entry to CHANGELOG.md and stop.