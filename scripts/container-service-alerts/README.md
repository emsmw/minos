# Homelab Container Monitoring and Alerting System 🖥️

A lightweight, production-style Docker container monitoring system built in Python for self-hosted homelab infrastructure. Monitors container health, detects state changes, delivers real-time Discord alerts, and StatusCake heartbeat integration for server uptime verification.

## The Problem I Solved

I run a self-hosted media server stack on a home Debian server (hostname **Minos**) all managed via Docker. I needed a reliable way to know **immediately** when a container went down, without being spammed with repeated alerts for the same issue.

Commercial monitoring solutions felt like overkill. I built this instead.

## Features

- 🐳 **Docker container monitoring** — checks all containers on the host
- 🚨 **Discord alerts** — instant notification when a container goes down
- ✅ **Recovery detection** — notified when a container comes back online
- 🔁 **State tracking** — alerts only fire on **state changes**, not every run
- 💓 **StatusCake heartbeat** — server uptime verification every 5 minutes
- 🖥️ **Dual mode** — manual runs gives immediate status on terminal, silent for cron/systemd

## How It Works

```
Script runs (via cron or manually)
        │
        ▼
Connect to Docker daemon
Check all container states
        │
        ▼
Compare to previous state (.container_state.json)
        │
     ┌──┴──┐
     │     │
  Changed  No change
     │     │
     ▼     ▼
Discord   Silent
Alert     (no spam)
     │
     ▼
Save new state for next run
        │
        ▼
Ping StatusCake heartbeat (every 5 min)
```
## Discord Alerts

> _Screenshot of Discord alert when container goes down notification_

![Discord Alert Notification](alert.png)
> _Screenshot of Discord recovery notification_

![Discord Alert Notification](recovery.png)

## StatusCake Discord Alerts

> _Screenshot of StatusCake Discord server down notification_

![Discord Alert Notification](server_down.png)

> _Screenshot of StatusCake Discord server back up notification_

![Discord Alert Notification](server_up.png)


The script pings a StatusCake push monitor URL every 5 minutes. If the ping stops arriving because the server is down, StatusCake send alert independently.

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.11 | Core language |
| Docker SDK for Python | Container state inspection |
| requests | HTTP calls (Discord webhook, StatusCake) |
| colorama | Coloured terminal output |
| zoneinfo | Timezone-aware timestamps |
| json / os | State file management |
| systemd / cron | Scheduled execution |

## Setup

### Prerequisites

- any Linux host with Docker installed
- Python 3.11+
- Docker running on the host
- A Discord server with a webhook configured
- StatusCake account for heartbeat monitoring

### 1. Clone the repository

```bash
git clone https://github.com/emsmw/homelab-container-service-alerts.git
cd homelab-container-service-alerts
```

### 2. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Configure credentials

```bash
nano config_secret.py
```

Fill in your values:

```python
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/your_webhook_here"
STATUSCAKE__PUSH_URL = "https://push.statuscake.com/?PK=your_key_here"
```

### 4. Test manually

```bash
python3 main.py
```

You should see a formatted table of your container statuses in the terminal.

### 5. Set up automated monitoring

**systemd service:**

Create `/etc/systemd/system/minos-container-monitoring.timer`:

```ini
[Unit]
Description=Run Minos Container Monitoring Every 5 Minutes

[Timer]
OnCalendar=*-*-* *:00,05,10,15,20,25,30,35,40,45,50,55:00
AccuracySec=1s
Persistent=true

[Install]
WantedBy=timers.target
```

Create `/etc/systemd/system/minos-container-monitoring.service`:

```ini
[Unit]
Description=Minos Container Monitoring Service
After=docker.service

[Service]
Type=oneshot
User=yourusername
WorkingDirectory=/home/yourusername/minos-monitoring
ExecStart=/usr/bin/python3 /home/yourusername/minos-monitoring/check-container-status.py --cron

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable minos-container-monitoring.timer
sudo systemctl start minos-container-monitoring.timer
sudo systemctl status minos-container-monitoring.timer
```



## Usage

### Manual scan (only terminal output, no Discord)

```bash
check-container-status
```

Example output:

```
########################################
            SCAN COMPLETE              
########################################
CONTAINER NAME                 STATUS
-
jellyfin                       RUNNING
sonarr                         RUNNING
radarr                         RUNNING
prowlarr                       RUNNING
qbittorrent                    RUNNING
-

Summary: 5/5 containers running
Scan time: 2026-05-15 14:32:01 EDT
```

### Automated mode (cron/systemd — sends Discord alerts)

```bash
check-container-status --cron
```

In `--cron` mode:
- No terminal output
- Discord alert sent only if container state changed
- StatusCake heartbeat pinged every 5 minutes

## Containers State Tracking Logic
The script saves container states to `.container_state.json` after each run:

```json
{
    "jellyfin": "running",
    "sonarr": "running",
    "radarr": "exited",
    "prowlarr": "running",
    "qbittorrent": "running"
}
```

On the next run it compares current states against this file:

```
Container was running → now exited  = 🚨 ALERT
Container was exited  → now running = ✅ RECOVERY
Container unchanged                 = 🔇 Silent
```

## What I Learned
- Docker Python SDK for programmatic container management
- Designing stateful monitoring systems with JSON persistence
- Alert fatigue — why state tracking matters in production
- systemd timer units for scheduled tasks
- Defensive programming — handling corrupted state files gracefully
- External heartbeat monitoring as a watchdog pattern
- The difference between container `status` and health check `status` in Docker

## What's Next
- [ ] qBittorrent download stall detection
- [ ] Disk and memory threshold alerts
- [ ] Prometheus metrics endpoint
- [ ] Grafana dashboard
- [ ] Kubernetes migration
- [ ] and more..

## Why I Built This
I'm a network architect pivoting into Site Reliability Engineering. Building real monitoring tools for infrastructure I actually operate teaches me more than any tutorial. This project mirrors what I observed in day to day work, just on a smaller scale.

The skills practiced here:
- Infrastructure monitoring design
- Python automation
- Docker management
- Alert system design
- Linux system administration

