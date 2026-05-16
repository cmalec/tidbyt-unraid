# Tidbyt Unraid Monitor

A self-contained Docker app that displays Unraid server metrics on your [Tidbyt](https://tidbyt.com/) device.

## Features

- **Fully local** — runs entirely on your Unraid server (or any Docker host)
- **No cloud dependencies** — pushes directly to your Tidbyt over WiFi
- **Customizable metrics** — choose what to display and how often
- **Auto-scaling layout** — fonts resize dynamically based on how many metrics you enable
- **Auto-updating** — refreshes on your chosen interval

## How It Works

1. **Fetch** — The container queries your Unraid's native GraphQL API for the metrics you've enabled
2. **Render** — It builds a 64x32 WebP image using PIL: metric labels and values in a centered grid layout
3. **Push** — The image is pushed to your Tidbyt device via Tidbyt's HTTP API
4. **Repeat** — Sleeps for `UPDATE_INTERVAL` seconds and does it again

The renderer dynamically scales fonts to fit your chosen metrics. Fewer metrics = bigger text. More metrics = compact layout.

## Supported Metrics

| Metric    | Label      | Description                 |
|-----------|------------|-----------------------------|
| `cpu`     | CPU        | CPU load percentage         |
| `ram`     | RAM        | RAM usage percentage        |
| `array`   | ARR        | Array state + capacity used |
| `temps`   | TMP        | Average disk temperature    |
| `docker`  | DKR        | Running / total containers  |
| `vms`     | VM         | Running / total VMs         |
| `uptime`  | UP         | Server uptime (e.g. `5d3h`) |
| `network` | *hostname* | Short hostname display      |

**Note:** Only the first 4 metrics are displayed. The renderer uses a grid layout:
- 1 metric → full screen
- 2 metrics → side by side
- 3 metrics → top half + bottom row split
- 4 metrics → 2×2 grid

## Quick Start

### 1. Prerequisites

- Unraid server running 7.2+ (native GraphQL API)
- Tidbyt device set up and connected
- Docker enabled/installed

### 2. Get Your Credentials

**Tidbyt:**

- Open the Tidbyt app → your device → Settings
- Note your **Device ID** and **API Key**

**Unraid:**

- Unraid 7.2+ exposes a native GraphQL API at `https://tower.local/graphql`
- Generate an API key in **Settings → Management Access → API Keys** in the Unraid web UI

### 3. Run with Docker Compose

```bash
# Clone the repo
git clone https://github.com/cmalec/tidbyt-unraid.git
cd tidbyt-unraid

# Edit environment variables
nano docker-compose.yml

# Pull and run from GitHub Container Registry
docker-compose up -d
```

Or use `docker run`:

```bash
docker run -d \
  --name tidbyt-unraid \
  --restart unless-stopped \
  -e UNRAID_URL=https://tower.local \
  -e UNRAID_API_KEY=your-key \
  -e TIDBYT_DEVICE_ID=your-device-id \
  -e TIDBYT_API_KEY=your-api-key \
  -e UPDATE_INTERVAL=3600 \
  -e METRICS=cpu,ram,array,uptime \
  ghcr.io/cmalec/tidbyt-unraid:latest
```

To build locally instead, use `docker build -t tidbyt-unraid:latest .` and update the image name in `docker-compose.yml`.

### 4. Environment Variables

| Variable           | Required | Default                | Description                                    |
|--------------------|----------|------------------------|------------------------------------------------|
| `UNRAID_URL`       | Yes      | —                      | Unraid server URL (e.g. `https://tower.local`) |
| `UNRAID_API_KEY`   | Yes      | —                      | API key for authentication                     |
| `TIDBYT_DEVICE_ID` | Yes      | —                      | Your Tidbyt device ID                          |
| `TIDBYT_API_KEY`   | Yes      | —                      | Your Tidbyt API key                            |
| `UPDATE_INTERVAL`  | No       | `3600` (1 hour)        | Seconds between updates                        |
| `METRICS`          | No       | `cpu,ram,array,uptime` | Comma-separated list of metrics                |
| `TEMP_UNIT`        | No       | `F`                    | Temperature unit (`C` or `F`)                  |
| `TZ`               | No       | `America/Los_Angeles`  | Timezone for logs                              |

### 5. Installing on Unraid

1. Go to **Apps** → search for "Tidbyt Unraid" (if published) or use the **Community Applications** template
2. Fill in the environment variables
3. Apply

Or manually add as a custom Docker container with the variables above.

## Customizing Metrics

To change what appears on your Tidbyt, edit the `METRICS` environment variable. It's a comma-separated list with no spaces.

**Examples:**

```bash
# Default: CPU, RAM, array, uptime
METRICS=cpu,ram,array,uptime

# Minimal: just CPU and RAM
METRICS=cpu,ram

# Full dashboard: everything
METRICS=cpu,ram,array,temps,docker,vms,uptime

# Docker-focused
METRICS=cpu,ram,docker,array
```

After changing `METRICS`, restart the container:

```bash
docker-compose restart tidbyt-unraid
```

The layout auto-scales. With 1-2 metrics you get large readable text. With 5+ it compacts down to fit everything. Percentage metrics (`cpu`, `ram`, `array`) show a colored mini
bar. Non-percentage metrics (`docker`, `vms`, `uptime`, `network`, `temps`) show the value only.

## Building Locally

```bash
docker build -t tidbyt-unraid:latest .
docker run --rm -it --env-file .env tidbyt-unraid:latest
```

## Troubleshooting

**Connection refused to Unraid:**

- Verify `UNRAID_URL` points to your Unraid server (default: `https://tower.local`)
- Ensure the API key is valid in **Tools → API Keys**

**Push fails:**

- Double-check your `TIDBYT_DEVICE_ID` and `TIDBYT_API_KEY`
- Ensure your Tidbyt is online and connected to WiFi

**Self-signed certificate errors:**

- The app disables SSL verification for Unraid connections (Unraid uses self-signed certs by default)
