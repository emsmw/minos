# Homelab Resource Checker

A modular Python command-line utility designed to monitor server hardware utilization (CPU, memory, and disk percentages) in real time. No external monitoring stack, no agents, no dashboards — just a script you run that gives you a clean, color-coded snapshot of system health.


```
================================================================================
                         CPU MEMORY DISK STATUS
================================================================================
[CPU USAGE PER CORE]
 Core  1 [████                ]  18.2% | Core  5 [██████████          ]  49.1%
 Core  2 [██                  ]   9.4% | Core  6 [███                 ]  14.0%
 ...

[MEMORY USAGE]
Total Memory:  16.0 GB
Used Memory :   6.2 GB
Free Memory :   9.8 GB
[███████             ]  39% used

[DISK USAGE]
sda1            [████████████                                      ] 24% used
Scan time: 2026-07-10 14:32:01 EDT
```

## Project Structure

```text
homelab-cpu-disk-mem-usage-alerts/
├── config_secret.py     # Sensitive configurations/credentials
├── main.py              # Main execution script
├── requirements.txt     # Python dependencies
├── .gitignore          # Git exclusion rules
├── monitors/            # Modular hardware monitoring scripts
└── .venv/               # Isolated virtual environment
```

## Features

- **Per-core CPU usage** — visual bar graph for every core, split into two columns for readability on wide terminals
- **Memory usage** — total / used / free in GB, plus a usage bar
- **Disk usage** — automatically discovers all mount points under `/mnt` and reports usage per mount
- **Threshold-based color coding** — usage bars/percentages turn red when they cross configurable warning thresholds, green otherwise
- **Timestamped output** — every scan is stamped with local time (`America/Toronto`, via `zoneinfo`)

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/emsmw/homelab-resource-monitor.git
cd homelab-resource-monitor
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create your local config

This project reads secrets/thresholds from a `config_secret.py` file that is **not** committed to the repo. Create one in the project root:

```python
# config_secret.py
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/your/webhook/url"
CPU_WARNING_PERCENT = your_desired_percentage
MEMORY_WARNING_PERCENT = your_desired_percentage
DISK_WARNING_PERCENT = your_desired_percentage
```

Add `config_secret.py` to `.gitignore` so you never accidentally commit real webhook URLs or thresholds.

### 5. Run it

```bash
python3 status.py
```

## What I Learned

- **Working with `psutil` for real system introspection** — pulling per-core CPU, memory, and disk metrics rather than just reading `/proc` by hand gave me a much better feel for what monitoring tools are actually doing under the hood.
- **Timezone-aware timestamps in Python** — using `zoneinfo` instead of naive `datetime` objects, and why that distinction actually matters once you're correlating logs across systems.
- **Structuring a small multi-module CLI project** — splitting CPU/memory/disk logic into their own modules instead of one big script, and importing shared config cleanly across files.
- **Terminal UI without a framework** — building readable, aligned, color-coded output using nothing but string formatting and `colorama`, which forced me to actually think about layout math (bar lengths, column alignment, percentage-to-character conversion) instead of leaning on a charting library.
- **Keeping secrets out of version control** — separating `config_secret.py` from the codebase and treating thresholds/webhooks as local configuration, not hardcoded values.
