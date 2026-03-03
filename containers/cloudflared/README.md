# Cloudflare Tunnel Setup

Expose totalSimulation publicly via Cloudflare Tunnel without opening firewall ports.

## Prerequisites

- A Cloudflare account with a domain
- `cloudflared` CLI installed locally (for initial tunnel creation)

## Steps

### 1. Create the tunnel

```bash
cloudflared tunnel login
cloudflared tunnel create totalsimulation
```

This creates a tunnel and outputs a **Tunnel ID** (UUID).

### 2. Place the credentials file

Copy the generated credentials JSON into the project:

```bash
cp ~/.cloudflared/<TUNNEL_ID>.json containers/cloudflared/credentials.json
```

> This file is gitignored and must never be committed.

### 3. Edit the config

Open `containers/cloudflared/config.yml` and replace:
- `<YOUR_TUNNEL_ID>` with the UUID from step 1
- `<YOUR_DOMAIN>` with your hostname (e.g., `sim.example.com`)

### 4. Route DNS

```bash
cloudflared tunnel route dns totalsimulation sim.example.com
```

### 5. Enable authentication

Before exposing publicly, enable JWT auth:

```env
# .env
AUTH_ENABLED=true
JWT_SECRET=<generate-a-strong-random-secret>
```

### 6. Start with tunnel profile

```bash
docker compose --profile tunnel up -d
```

The `cloudflared` container will start alongside the other services.

### Verify

```bash
docker compose --profile tunnel ps
curl https://sim.example.com/health
```

### Stop

```bash
docker compose --profile tunnel down
```

Without the `--profile tunnel` flag, `docker compose up -d` will **not** start the tunnel container.
