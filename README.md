# minos

Infrastructure-as-code and monitoring for my self-hosted homelab — a single bare-metal Debian 13 server (hostname `minos`) running a Docker-based media/services stack, Python-based monitoring and alerting, and a Jenkins CI/CD pipeline that gates changes by which part of the repo they touch.

This repo is the source of truth for everything running on the box: service definitions, alerting scripts, and the pipeline that validates them. 

## Architecture

```text
                     ┌─────────────┐
   git push  ──────▶ │   GitHub    │
                     │ (dev → main)│
                     └──────┬──────┘
                            │ PR merge to main
              ┌─────────────┼─────────────┐
              ▼                           ▼
      ┌───────────────┐           ┌───────────────┐
      │    Jenkins     │           │   Portainer    │
      │ path-scoped CI │           │  GitOps stacks │
      └───────┬────────┘           └───────┬────────┘
              │ syntax/dep checks          │ pull + recreate
              ▼                            ▼
      scripts/ validated          docker-stacks/ deployed
                                            │
                                            ▼
                              ┌─────────────────────────┐
                              │   minos (Debian 13)      │
                              │  arr · jellyfin · navidrome
                              │  homarr · grafana · prometheus
                              │  jenkins                 │
                              └─────────────────────────┘
                                            ▲
                              systemd timer (5 min)
                              container-service-alerts
                                    → Discord / StatusCake
```

Git is the single source of truth on both sides of this diagram: Jenkins validates code changes, Portainer deploys infrastructure changes — neither one touches the box by hand.

## Repo structure

```text
minos/
├── Jenkinsfile              # CI pipeline — path-scoped stages
├── ansible/                 # Host provisioning — base packages, Docker, firewall
│   ├── inventory/
│   ├── roles/
│   │   ├── base/
│   │   ├── docker/
│   │   └── firewall/
│   └── site.yml
├── docker-stacks/           # docker-compose definitions, one folder per stack
│   ├── arr/                 # VPN'd media-acquisition stack
│   ├── grafana/
│   ├── homarr/               # dashboard / homepage
│   ├── jellyfin/
│   ├── jenkins/              # Jenkins controller + custom Python build agent
│   ├── navidrome/
│   └── prometheus/
└── scripts/                  # Standalone Python monitoring tools
    ├── container-service-alerts/   # Docker container health monitoring + Discord alerts + StatusCake heartbeat when the server itself is down
    └── cpu-disk-mem-alerts/        # CPU/memory/disk usage monitoring
```

## Host provisioning (`ansible/`)

Before any Docker stack runs, the `minos` host itself is provisioned with a single Ansible playbook (`ansible/site.yml`) rather than by hand — this is what makes the underlying box reproducible, not just the services on top of it. Three roles, applied in order:

- **`base`** — updates the apt cache and installs the packages the rest of the system assumes are present (`curl`, `git`, `unattended-upgrades`).
- **`docker`** — installs Docker via the official convenience script, but only if it isn't already present (`command: docker --version` is checked first, so re-running the playbook never reinstalls), and adds the host user to the `docker` group.
- **`firewall`** — installs and enables `ufw` with a default-deny policy, explicitly allowing only the ports each running stack actually needs: SSH (`22`), Jenkins UI/agent (`8080`/`50000`), Prometheus (`9090`), Navidrome (`4533`), Jellyfin (`8096`), Homarr (`7575`), Grafana (`3000`), Portainer (`8000`/`9443`), Radarr (`7878`), Sonarr (`8989`), and the `gluetun`-routed ports for the VPN'd side of the `arr` stack (`6881`, `8085`, `8191`, `9696`).

The playbook is run from a separate control node (a laptop, over WSL) against `minos` as the managed node, connecting over SSH with a dedicated key scoped only to Ansible — not the same key used for GitHub access. Keeping control node and managed node separate now is deliberate: it's the same pattern needed the moment a second host (e.g. a cloud build agent or offsite backup target) joins the inventory, so nothing about the setup has to change later, just an added entry in `inventory/hosts.yml`.

Verified idempotent before merging: a second run of `ansible-playbook site.yml` against an already-provisioned host reports `changed=0` across all 23 tasks — confirming the playbook only ever converges state, it doesn't redo work or drift the host on repeat runs.

## Services (`docker-stacks/`)

| Stack | Image(s) | Port(s) | Purpose |
|---|---|---|---|
| `arr` | `gluetun`, `qbittorrent`, `prowlarr`, `sonarr`, `radarr`, `flaresolverr`, `deunhealth` | `8085`, `6881`, `9696`, `8191` (via `gluetun`); `8989` (Sonarr), `7878` (Radarr) | VPN-gated media acquisition — `qbittorrent`, `prowlarr`, and `flaresolverr` route through `gluetun` since they either handle raw torrent traffic or make outbound indexer requests; `sonarr`/`radarr` sit outside the VPN since they only orchestrate the other services and never touch tracker/torrent traffic directly. `deunhealth` auto-restarts unhealthy containers. |
| `jellyfin` | `linuxserver/jellyfin` | `8096` | Media server |
| `navidrome` | `deluan/navidrome` | `4533` | Self-hosted music streaming |
| `homarr` | `ajnart/homarr` | `7575` | Homepage/dashboard for the services on the box |
| `grafana` | `grafana/grafana` | `3000` | Dashboards for metrics |
| `prometheus` | `prom/prometheus` | `9090` | Metrics collection |
| `jenkins` | `jenkins/jenkins:lts` + custom `python-agent` | `8080` (UI), `50000` (agent) | CI/CD controller; the agent image bundles Python 3, pip, venv, git, and curl for running the pipeline below |

Each stack is an independent `docker-compose.yml`. Where a stack needs secrets or environment-specific config (currently `arr`, for its WireGuard credentials), a `.env.example` is provided — copy it to `.env` and fill in real values before starting the stack. Never commit the filled-in `.env` (already covered by `docker-stacks/.gitignore`).

## GitOps with Portainer

None of the stacks above are started manually with `docker compose up -d` on the box — Portainer manages all seven as **GitOps stacks**, pulling their compose definitions directly from this repo instead of storing them in Portainer's own internal database. I moved to this model specifically to kill config drift: previously a stack's "real" definition only existed inside Portainer's UI, with no history and no way to tell what changed between deployments.

How it's wired up:

- Each stack in Portainer is configured to track this repository at a specific path (e.g. `docker-stacks/jellyfin`), so the compose file in git *is* the deployed definition — there's no drift between "what's in the repo" and "what's actually running."
- Redeploying a stack after a change is a pull-and-recreate from git, not a manual edit in the Portainer UI. This repo is the only place stack definitions get edited.
- Secrets never live in the tracked compose files. Anything sensitive — e.g. the `arr` stack's `WIREGUARD_PRIVATE_KEY` and `WIREGUARD_ADDRESSES` — is injected as a Portainer environment variable at the stack level, referenced in the compose file as `${VARIABLE_NAME}`. That keeps credentials out of git entirely while still letting the compose file itself be fully public.
- Changes flow through a `dev` → `main` branch workflow with pull requests: stack/script edits land on `dev`, get reviewed via PR, and only reach `main` (what Portainer/Jenkins actually track) once merged.

This setup was migrated from an earlier state where all seven stacks lived purely inside Portainer's internal storage with no version history — moving them to GitOps means every config change is now a commit, diffable and revertible like any other code change, and a full redeploy of the box's services is just "point Portainer at this repo."

## Monitoring & alerting (`scripts/`)

Two independent Python tools, each with its own detailed README ([container-service-alerts](scripts/container-service-alerts/README.md), [cpu-disk-mem-alerts](scripts/cpu-disk-mem-alerts/README.md)):

- **`container-service-alerts`** — polls the Docker daemon for container state using the Docker SDK, fires a Discord webhook alert only on state changes (up→down, down→up), and pings a StatusCake heartbeat URL every 5 minutes for independent uptime verification. State-change-only alerting was a deliberate choice: an earlier naive version alerted on every poll and became noise I started ignoring, which defeats the point of alerting. Runs on the host via the `minos-container-monitoring.timer`/`.service` systemd units, every 5 minutes.
- **`cpu-disk-mem-alerts`** — modular CPU/memory/disk usage checker built on `psutil`, with color-coded terminal bar graphs and configurable warning thresholds. Exposed on the host as the `resource-check` command.

Both read secrets and thresholds from a local `config_secret.py` that is gitignored — never committed.

**In practice:** since switching to state-change-only Discord alerts, alert volume dropped to just real up/down transitions instead of one message per 5-minute poll — the signal that used to get lost in noise is now something I actually read.

## CI/CD

The `Jenkinsfile` runs on a custom Jenkins agent (`docker-stacks/jenkins/agents/python-agent`) and scopes each stage to the part of the repo that changed, so a change to one script doesn't trigger a build of the other. I chose Jenkins over a hosted CI (e.g. GitHub Actions) specifically to get hands-on with self-hosted agent management and Docker Cloud configuration, which is closer to what larger infra teams run in-house.

- Changes under `scripts/container-service-alerts/**` → install deps, `py_compile` syntax check on `check-container-status.py`
- Changes under `scripts/cpu-disk-mem-alerts/**` → install deps, `py_compile` syntax check on `main.py`

This keeps the pipeline fast and makes it obvious from the build log which part of the homelab actually changed.

## Tech stack

| Layer | Tools |
|---|---|
| Host OS | Debian 13 (bare metal) |
| Provisioning | Ansible (host bootstrap: base packages, Docker install, `ufw` firewall) |
| Orchestration | Docker / Docker Compose, Portainer (GitOps stack deployments) |
| CI/CD | Jenkins, custom Python build agent |
| Monitoring | Python (`psutil`, `docker` SDK, `colorama`), Prometheus, Grafana |
| Alerting | Discord webhooks, StatusCake heartbeat |
| Networking | WireGuard (via `gluetun`) for the media stack; each service exposed on its own port on the LAN (see [Services](#services-docker-stacks) for the full port list) |