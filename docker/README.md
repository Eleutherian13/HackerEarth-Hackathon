# Docker Configuration

This folder contains Docker Compose configuration and supporting service files for the LAOS application.

## Files Overview

### Core Configuration

- **nginx.conf**: Reverse proxy and web server configuration for API gateway and static file serving

### Directory Structure

- `nginx/` - Nginx reverse proxy configuration
- `postgres/` - PostgreSQL configuration (if used)
- `redis/` - Redis configuration (if used)

## Quick Start

### Development

```bash
# Build and run all services locally
docker compose up --build

# Services will be available at:
# - Frontend: http://localhost:3000
# - API: http://localhost:8000/api
# - Database: localhost:5432
# - Redis: localhost:6379
```

### Production

```bash
# Deploy with production overrides
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Deploy script available at scripts/deploy-docker.sh
bash scripts/deploy-docker.sh
```

## Environment Variables

- `.env.example` - Template with all configuration options
- `.env.development` - Development defaults
- `.env.staging` - Staging environment configuration
- `.env` - Created locally from .env.development or .env.staging

## Service Details

### Backend (FastAPI)

- **Image**: Python 3.11-slim
- **Port**: 8000
- **Features**: Multi-stage build, health checks, migrations
- **Dependencies**: PostgreSQL, Redis

### Frontend (React + Vite)

- **Image**: Nginx Alpine
- **Port**: 3000 (dev), 80 (prod)
- **Features**: Build-time env injection, gzip compression, security headers
- **Dependencies**: Backend API

### Worker (Celery)

- **Image**: Python 3.11-slim
- **Features**: Async task processing, same deps as backend
- **Dependencies**: PostgreSQL, Redis

### Database (PostgreSQL)

- **Image**: postgres:16-alpine
- **Port**: 5432
- **Volume**: postgres_data

### Cache (Redis)

- **Image**: redis:7-alpine
- **Port**: 6379
- **Volume**: redis_data

### Reverse Proxy (Nginx)

- **Image**: nginx:alpine
- **Ports**: 80, 443
- **Features**: API gateway, rate limiting, SSL/TLS

## Configuration Files

### docker-compose.yml

Development/default configuration with all services.

### docker-compose.prod.yml

Production overrides: replicas, resource limits, logging, secrets.

### docker-compose.override.yml

Automatically applied in local development: volume mounts, dev environment variables.

## Deployment

See `scripts/deploy-docker.sh` for automated deployment steps including:

1. Image building
2. Registry push (optional)
3. Service deployment
4. Health verification
5. Database migrations

## Networking

- Services communicate via internal Docker network
- External access through Nginx reverse proxy (ports 80/443)
- API rate limited at proxy level

## Logging

- All services output to stdout/stderr
- Production: JSON file driver with rotation (10MB, 3 files)
- Development: Docker logs aggregation with text format

## Health Checks

- Backend: HTTP GET /api/v1/health
- Database: pg_isready command
- Redis: redis-cli ping

## For More Information

See the root directory Docker configuration files:

- `docker-compose.yml` - Full development configuration
- `docker-compose.prod.yml` - Production deployment overrides
- `backend/Dockerfile` - Backend image definition
- `frontend/Dockerfile` - Frontend image definition
- `worker/Dockerfile` - Worker image definition
