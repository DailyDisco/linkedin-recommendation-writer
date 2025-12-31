# Blue-Green Deployment Setup

Zero-downtime deployment for LinkedIn Recommendation Writer, integrated with your existing appstack at `/srv/vault/appstack/`.

## Architecture

```
User → Cloudflare → Caddy (appstack) → [app-blue:8000]  (active)
                                    → [app-green:8000] (standby)
                                    → [postgres:5432]  (linkedin-internal)
                                    → [redis:6379]     (linkedin-internal)
```

The app containers connect to both:
- `linkedin-internal` - Private network for database/cache
- `appstack_web` - External network where Caddy lives

## Quick Start

### 1. Create Deployment Directory

```bash
# Create deployment directory
mkdir -p /srv/linkedin-recommender/{scripts,backups,logs}

# Copy files
cp -r deployment/blue-green/* /srv/linkedin-recommender/

# Set permissions
chmod +x /srv/linkedin-recommender/scripts/*.sh

# Create production environment file
cp /srv/linkedin-recommender/.env.production.example /srv/linkedin-recommender/.env.production
nano /srv/linkedin-recommender/.env.production  # Edit with your values
```

### 2. Update Appstack Caddy

**Add volume mount for active-deployment directory:**

Edit `/srv/vault/appstack/docker-compose.yml`:

```yaml
caddy:
  volumes:
    - ./caddy/Caddyfile:/etc/caddy/Caddyfile:ro
    - ./caddy/data:/data
    - ./caddy/config:/config
    - ./caddy/certs:/etc/caddy/certs:ro
    - ./caddy/active-deployment:/etc/caddy/active-deployment  # ADD THIS LINE
```

**Create the directory and initial marker:**

```bash
mkdir -p /srv/vault/appstack/caddy/active-deployment
touch /srv/vault/appstack/caddy/active-deployment/linkedin-blue
```

**Add site blocks to Caddyfile:**

Append the contents of `caddyfile.snippet` to `/srv/vault/appstack/caddy/Caddyfile`.

**Restart Caddy:**

```bash
cd /srv/vault/appstack
docker compose up -d caddy
```

### 3. Add DNS in Cloudflare

1. Go to Cloudflare Dashboard → DNS
2. Add A record:
   - Name: `linkedin`
   - Content: Your server IP
   - Proxy: Enabled (orange cloud)

### 4. Initial Deployment

```bash
cd /srv/linkedin-recommender

# Start infrastructure
docker compose -f docker-compose.blue-green.yml --env-file .env.production up -d postgres redis

# Wait for postgres
sleep 10

# Build and start blue
docker compose -f docker-compose.blue-green.yml --env-file .env.production build app-blue
docker compose -f docker-compose.blue-green.yml --env-file .env.production up -d app-blue

# Run initial migrations
docker exec linkedin-recommender-app-blue sh -c "cd /app/backend && alembic upgrade head"

# Verify
./scripts/health-check.sh
```

## Daily Operations

### Deploy New Version

```bash
make deploy
# or
./scripts/deploy.sh
```

### Rollback

```bash
make rollback
```

### Check Health

```bash
make health
```

### View Logs

```bash
make bg-logs-blue   # Blue deployment
make bg-logs-green  # Green deployment
```

## File Structure

```
/srv/linkedin-recommender/
├── docker-compose.blue-green.yml
├── .env.production
├── scripts/
│   ├── deploy.sh
│   ├── rollback.sh
│   └── health-check.sh
└── backups/

/srv/vault/appstack/caddy/
├── Caddyfile              # Add linkedin.* site blocks
└── active-deployment/
    └── linkedin-blue      # Marker file (or linkedin-green)
```

## Networks

| Network | Purpose |
|---------|---------|
| `linkedin-internal` | Private network for postgres/redis (internal: true) |
| `appstack_web` | External network connecting to Caddy |

## Environment Variables

Key variables in `.env.production`:

| Variable | Description |
|----------|-------------|
| `REPO_PATH` | Path to git repository |
| `DATABASE_URL` | PostgreSQL connection string |
| `POSTGRES_PASSWORD` | Database password |
| `GITHUB_TOKEN` | GitHub API token |
| `GEMINI_API_KEY` | Google Gemini API key |
| `SECRET_KEY` | JWT secret |
| `ALLOWED_ORIGINS` | `https://linkedin.greenlightbase.com` |

## How Blue-Green Works

1. **Current state**: Blue is active, serving traffic
2. **Deploy**: Build and start Green
3. **Health check**: Verify Green is healthy
4. **Migrate**: Run database migrations
5. **Switch**: Touch `/srv/vault/appstack/caddy/active-deployment/linkedin-green`
6. **Traffic**: Caddy routes to Green
7. **Rollback**: Touch `linkedin-blue` to switch back

## Troubleshooting

### Container can't reach Caddy network

```bash
# Verify appstack_web network exists
docker network ls | grep appstack_web

# If not, start appstack first
cd /srv/vault/appstack && docker compose up -d
```

### Caddy not routing traffic

```bash
# Check marker file
ls -la /srv/vault/appstack/caddy/active-deployment/

# Check Caddy can reach containers
docker exec caddy ping linkedin-recommender-app-blue

# Reload Caddy
docker exec caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
```

### Database connection issues

```bash
# Check postgres is healthy
docker exec linkedin-recommender-postgres pg_isready -U postgres

# Check network connectivity
docker exec linkedin-recommender-app-blue ping linkedin-recommender-postgres
```
