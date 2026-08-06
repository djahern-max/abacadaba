# Hardening checklist

Merge this into `DEPLOYMENT.md` once the Droplet architecture replaces the
App Platform sections.

Ordered by how much each item actually reduces risk, not by how much work it
is. The first section is the one that matters most for this project's history.

---

## 1. Supply chain — the build never runs on this box

A malicious npm package executes its `postinstall` script at install time, as
whoever ran `npm install`, on whatever machine ran it. No firewall rule
prevents this, because nothing broke in: the build invited it.

- [ ] `npm install` and `npm run build` run on the laptop or in CI. **Never on
      the Droplet.** Node is not installed on the Droplet at all.
- [ ] Deploys ship the built `dist/` directory via rsync. Static HTML, CSS, and
      JS have no lifecycle hooks and no runtime.
- [ ] `package-lock.json` is committed, and installs use `npm ci` (which honours
      the lockfile exactly) rather than `npm install`.
- [ ] Consider `npm ci --ignore-scripts` locally. Vite and React don't need
      lifecycle scripts; if a build breaks without them, that's worth knowing.
- [ ] `npm audit` before adding any dependency. `CLAUDE.md` already requires
      justifying every new one — this is the security half of that rule.
- [ ] Python side: `requirements.txt` pins every version. Keep it that way.

**Why this is first:** the previous compromise on an earlier project was most
likely a corrupt npm package. Everything below defends against attackers
knocking on the door. This defends against the thing that already got in once.

---

## 2. SSH

The highest-volume automated attack surface on any Droplet.

- [ ] Non-root user with sudo created; root login disabled.
- [ ] Key-only authentication. In `/etc/ssh/sshd_config`:
      ```
      PasswordAuthentication no
      PermitRootLogin no
      KbdInteractiveAuthentication no
      AllowUsers deploy
      ```
- [ ] **Confirm key login works in a second terminal before restarting sshd.**
      Locking yourself out of a fresh Droplet is recoverable via the console,
      but it's an annoying hour.
- [ ] `sudo systemctl restart ssh`
- [ ] fail2ban installed. Understand it's mostly log hygiene once passwords are
      off — it stops the noise, not the threat.
- [ ] `~/.ssh/authorized_keys` reviewed. Re-check periodically; adding a key is
      how an attacker keeps access after you patch the way they got in.

---

## 3. Firewall — and the Docker bypass

ufw is short. The trap is that it can look correct while being bypassed.

- [ ] ```
      sudo ufw default deny incoming
      sudo ufw default allow outgoing
      sudo ufw limit 22/tcp
      sudo ufw allow 80/tcp
      sudo ufw allow 443/tcp
      sudo ufw enable
      ```
      `limit` rather than `allow` on 22 throttles repeated connection attempts.
- [ ] **DigitalOcean Cloud Firewall enabled with the same three ports.** This
      runs at their network edge, before packets reach the box, so Docker
      cannot bypass it. Free, and the real backstop for the item below.
- [ ] No `ports:` key on the `db` service in `docker-compose.prod.yml`.
- [ ] The `api` service publishes to `127.0.0.1:8080`, never `0.0.0.0:8080`.
- [ ] The Docker daemon API is not exposed. Never enable TCP 2375/2376 —
      unauthenticated Docker socket access is instant root and is among the
      most-scanned ports on the internet.
- [ ] `/var/run/docker.sock` is not mounted into any container. That is
      container escape by design.

### Verify from outside the box

On-box checks tell you what you configured. Only an external scan tells you
what's actually reachable.

```bash
# from your laptop
nc -zv abacadaba.com 5432     # want: refused or timeout
nc -zv abacadaba.com 8080     # want: refused or timeout
nmap -Pn -p 22,80,443,2375,2376,5432,8080 abacadaba.com
```

- [ ] 5432 unreachable
- [ ] 8080 unreachable
- [ ] 2375/2376 unreachable
- [ ] On-box, `sudo ss -tlnp` shows `127.0.0.1:8080` and nothing on
      `0.0.0.0:5432`

---

## 4. Credentials

- [ ] Postgres password generated with `openssl rand -base64 32`. The local
      `docker-compose.yml` uses `abacadaba/abacadaba`, which is fine on
      localhost and catastrophic anywhere else. Do not carry it over.
- [ ] `.env` on the Droplet is `chmod 600` and owned by the deploy user.
- [ ] `.env` is in `.gitignore` and has never been committed. If it ever was,
      rotate the Spaces keys — git history is forever.
- [ ] Spaces keys are a dedicated pair for this app, so they can be rotated
      without touching anything else.
- [ ] The Space itself is still private. Feature 003's acceptance criteria
      included proving an unsigned URL returns AccessDenied — re-verify in
      production.

---

## 5. Containment

Assume something eventually gets in. Limit what it can do.

- [ ] `security_opt: no-new-privileges:true` on both services.
- [ ] `cap_drop: ALL` on `api`. (Not on `db` — the postgres entrypoint needs
      CHOWN/SETUID/SETGID to fix data-directory ownership before dropping
      privileges, and dropping ALL breaks first boot.)
- [ ] `read_only: true` on `api`, with `/tmp` as `noexec` tmpfs for upload
      spooling. **If the API won't start or uploads break, remove `read_only`
      first when debugging** — it's the most likely culprit for a surprising
      permission error.
- [ ] `cpus: 1.0` and `mem_limit` set. A CPU cap is an underrated anti-miner
      control: it can't take the box down, and pegged CPU becomes an alertable
      signal instead of ambient load.
- [ ] `pids_limit` set on both services.
- [ ] The `backend` network is `internal: true`, so the database container has
      no route to the internet — it cannot fetch a payload or exfiltrate.
- [ ] The Dockerfile still runs as `appuser`. When someone later suggests
      running as root "just to fix the permissions," the answer is no.
- [ ] Log rotation configured (`max-size`, `max-file`) so a chatty failure
      can't fill the disk.

---

## 6. Patching and noticing

- [ ] `unattended-upgrades` installed **and verified running** —
      `systemctl status unattended-upgrades`. Installed-but-inactive is the
      common failure.
- [ ] Base images rebuilt periodically. `python:3.12-slim` and `postgres:16`
      accumulate CVEs; `docker compose build --pull` picks up fixes.
- [ ] DigitalOcean monitoring alert on sustained high CPU. This is your miner
      tripwire and it's free.
- [ ] Bandwidth graph glanced at occasionally. Egress spikes mean either the
      app got popular or something is talking to a pool.

### Where to look when something feels wrong

```bash
top                                  # unfamiliar process eating CPU
docker ps                            # container you didn't start
crontab -l && sudo crontab -l        # per-user and root cron
ls -la /etc/cron.*                   # the classic persistence spot
systemctl list-timers                # the modern one
cat ~/.ssh/authorized_keys           # keys you didn't add
sudo ss -tlnp                        # unexpected listener
```

---

## 7. Backups — Feature 013, noted here so it isn't forgotten

Postgres runs in a container on this box, so backups are entirely yours. This
was the accepted tradeoff of not using a managed cluster.

- [ ] Nightly `pg_dump` on a cron.
- [ ] **Dumps shipped off-box** — to Spaces, via a separate key with write-only
      access to a backups bucket. A dump on the same disk as the database is
      not a backup.
- [ ] Old dumps pruned so the disk doesn't fill.
- [ ] **A restore actually performed into a scratch database.** Feature 013
      requires this explicitly, and it's the step everyone skips. An untested
      backup is not a backup.
- [ ] Retention period documented in `OPERATIONS.md`.

Accepted risk: no point-in-time recovery. A box failure costs up to 24 hours of
data. Fine for seeded lessons and a handful of accounts; revisit if this ever
holds data you'd be upset to lose.

---

## Deliberately not doing (yet)

**Default-deny egress filtering.** This is the control that genuinely neuters a
miner, since it can't reach a pool. It's also high-friction: you'd allowlist
DNS, NTP, apt, Docker Hub, PyPI, and the Spaces endpoint, and it breaks in
confusing ways at the worst possible moment. Modern miners also tunnel over
443, so it's not a complete answer.

Skipped for now given a capped-CPU container, an `internal: true` database
network, and a three-port inbound surface. It is the right escalation if this
box ever gets hit.
