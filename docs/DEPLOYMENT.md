# Deployment Guide

Production deployment, monitoring, and operational procedures for LAOS.

## Pre-Deployment Checklist

Before deploying to production, verify all items:

- [ ] All tests pass locally: `pytest` and `npm test`
- [ ] Code reviewed and approved by team lead
- [ ] Security scan completed: OWASP, dependency vulnerabilities
- [ ] Database migrations tested on staging
- [ ] Environment variables configured and validated
- [ ] SSL/TLS certificates obtained
- [ ] Load testing completed (expected traffic)
- [ ] Disaster recovery plan documented
- [ ] Backup strategy configured
- [ ] Monitoring and alerting configured
- [ ] Team trained on deployment process

## Deployment Environments

LAOS supports three deployment configurations:

### Development (`docker-compose.yml`)
- Single-instance services
- Debug logging enabled
- Hot-reload for code changes
- Minimal resources (development machine)
- **Not suitable for production**

### Staging (`docker-compose.yml` + override)
- Test environment for pre-production validation
- Multiple replicas for load testing
- Production-like configuration
- Real TLS certificates (optional)
- Full monitoring and logging

### Production (`docker-compose.prod.yml`)
- High availability setup
- Multiple replicas with load balancing
- Full monitoring and alerting
- Production security hardening
- Automated scaling (optional with Kubernetes)
- Disaster recovery configured

## Docker Compose Deployment

### Basic Deployment

```bash
# 1. Clone repository
git clone <repository-url>
cd laos

# 2. Load environment configuration
cp .env.production .env

# 3. Edit environment variables
nano .env
# Configure:
# - ADMIN_EMAIL / ADMIN_PASSWORD
# - SECRET_KEY (generate: openssl rand -hex 32)
# - DATABASE_URL (production database)
# - REDIS_URL (production Redis)
# - OPENAI_API_KEY (for extraction)
# - ALLOWED_HOSTS (your domain)

# 4. Pull latest images
docker pull <registry>/laos-backend:latest
docker pull <registry>/laos-frontend:latest

# 5. Start services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 6. Verify deployment
bash scripts/health-check.sh
```

### Health Check
```bash
# Manual verification
curl https://yourdomain.com/api/v1/health
# Should return: {"status":"healthy","database":"connected",...}

# Or use provided script
bash scripts/health-check.sh
```

### Logs Monitoring
```bash
# View logs from all services
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres

# View last 100 lines
docker compose logs --tail 100

# Logs with timestamps
docker compose logs --timestamps

# Save logs to file
docker compose logs > deployment.log 2>&1
```

## Database Configuration

### PostgreSQL Setup

#### Initial Setup
```bash
# 1. Create database
createdb laos_production

# 2. Create user with password
createuser laos_app --no-createdb --no-superuser
ALTER USER laos_app WITH PASSWORD 'strong_password_here';

# 3. Grant privileges
GRANT CONNECT ON DATABASE laos_production TO laos_app;
GRANT USAGE ON SCHEMA public TO laos_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO laos_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO laos_app;

# 4. Configure connection
# In .env:
DATABASE_URL=postgresql://laos_app:strong_password@db.example.com:5432/laos_production
```

#### Backup Strategy

**Daily Automated Backups:**
```bash
#!/bin/bash
# File: /usr/local/bin/backup-laos-db.sh
BACKUP_DIR="/backups/laos"
DB_NAME="laos_production"
DB_USER="laos_app"
DB_HOST="localhost"

# Create backup
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/laos_$(date +%Y%m%d_%H%M%S).sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "laos_*.sql.gz" -mtime +30 -delete

# Backup to S3 (optional)
aws s3 sync $BACKUP_DIR s3://my-backup-bucket/laos/
```

**Cron Schedule:**
```bash
# Daily at 2 AM
0 2 * * * /usr/local/bin/backup-laos-db.sh
```

**Restore from Backup:**
```bash
# Drop current database (WARNING: destructive!)
dropdb laos_production

# Create new empty database
createdb laos_production

# Restore from backup
gunzip < /backups/laos/laos_20240501_020000.sql.gz | psql laos_production
```

#### Connection Pooling

For high-traffic deployments, use PgBouncer:

```ini
# File: /etc/pgbouncer/pgbouncer.ini
[databases]
laos_production = host=localhost port=5432 dbname=laos_production

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 10
reserve_pool_size = 5
reserve_pool_timeout = 3
max_db_connections = 100

[console]
admin_users = postgres
```

### Data Retention Policies

| Data | Retention | Rationale |
|------|-----------|-----------|
| Extracted documents | 7 years | Indian compliance requirement |
| Audit logs | Indefinite | Legal accountability |
| Temporary files | 30 days | Storage optimization |
| User sessions | 30 days | Inactive user cleanup |
| API logs | 90 days | Troubleshooting window |

## SSL/TLS Configuration

### Using Let's Encrypt (Recommended)

```bash
# 1. Install Certbot
apt-get install certbot python3-certbot-nginx

# 2. Generate certificate
certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# 3. Configure Nginx (see below)

# 4. Auto-renewal (already configured)
systemctl enable certbot.timer
```

### Nginx Configuration

File: `docker/nginx/nginx.conf`

```nginx
upstream backend {
    server backend:8000;
    keepalive 32;
}

upstream frontend {
    server frontend:3000;
    keepalive 32;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=general:10m rate=60r/m;
limit_req_zone $http_x_real_ip zone=auth:10m rate=10r/m;

server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml+rss;
    gzip_min_length 1000;
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # API with rate limiting
    location /api/ {
        limit_req zone=general burst=20 nodelay;
        limit_req zone=auth burst=5 nodelay;
        
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint (no rate limit)
    location /api/v1/health {
        proxy_pass http://backend;
        access_log off;
    }
}
```

## Redis Configuration

### Persistence

```ini
# File: docker/redis/redis.conf
# Enable RDB snapshots
save 900 1
save 300 10
save 60 10000

# Enable AOF (Append-Only File) for durability
appendonly yes
appendfsync everysec
```

### Memory Management

```bash
# Set max memory limit
redis-cli CONFIG SET maxmemory 2gb

# Eviction policy (remove oldest if memory full)
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Persist configuration
redis-cli CONFIG REWRITE
```

### Backup

```bash
# Manual backup
redis-cli BGSAVE

# Restore from backup
redis-cli SHUTDOWN
cp /var/lib/redis/dump.rdb /var/lib/redis/dump.rdb.bak
redis-server
redis-cli BGREWRITEAOF
```

## Monitoring & Alerting

### Application Monitoring

```bash
# Health check endpoint
curl https://yourdomain.com/api/v1/health

# Response structure:
{
  "status": "healthy",
  "timestamp": "2024-05-01T10:30:00Z",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

### Logging Configuration

Set in `.env`:
```
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json             # json or text
LOG_FILE=/var/log/laos/app.log
```

View logs:
```bash
# Tail logs
tail -f /var/log/laos/app.log

# Search logs
grep "ERROR" /var/log/laos/app.log

# Export logs
tail -10000 /var/log/laos/app.log | gzip > laos_logs_$(date +%Y%m%d).log.gz
```

### Metrics Collection (Prometheus)

File: `docker/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Alert Configuration (AlertManager)

File: `docker/alertmanager/alertmanager.yml`

```yaml
global:
  resolve_timeout: 5m

route:
  receiver: 'ops-team'
  group_by: ['alertname', 'cluster', 'service']

receivers:
  - name: 'ops-team'
    email_configs:
      - to: 'ops@company.com'
        from: 'alerts@laos.company.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@company.com'
        auth_password: '{{ .Env.SMTP_PASSWORD }}'
    slack_configs:
      - api_url: '{{ .Env.SLACK_WEBHOOK_URL }}'
        channel: '#laos-alerts'
```

### Key Metrics to Monitor

| Metric | Alert Threshold | Action |
|--------|-----------------|--------|
| API Response Time (p95) | > 2s | Scale up backend replicas |
| Error Rate | > 1% | Check backend logs, restart if needed |
| Database Connection Pool | > 80% | Increase pool size or check queries |
| Redis Memory | > 80% | Monitor for memory leaks, scale up |
| Disk Free Space | < 20% | Archive old logs, cleanup uploads |
| CPU Usage | > 80% | Profile workload, optimize code |

## Scaling & Load Testing

### Horizontal Scaling

To run multiple backend replicas:

File: `docker-compose.prod.yml`

```yaml
services:
  backend:
    build: ./backend
    deploy:
      replicas: 3
    environment:
      - WORKERS=4
```

Then restart:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Load Testing

Install Apache Bench:
```bash
apt-get install apache2-utils
```

Run load test:
```bash
# 1000 requests, 50 concurrent
ab -n 1000 -c 50 https://yourdomain.com/api/v1/health
```

Expected results:
```
Requests per second:    150
Time per request:       330ms (mean)
Failed requests:        0
```

## Disaster Recovery

### RTO/RPO Targets

| Scenario | RTO | RPO |
|----------|-----|-----|
| Single service failure | 5 min | 0 min |
| Database failure | 30 min | 1 min |
| Data center failure | 1 hour | 5 min |
| Complete system failure | 4 hours | 1 hour |

### Failure Scenarios & Recovery

#### 1. Backend Service Crashes
```bash
# Auto-recovery with Docker
docker compose up -d backend
# Service restarts within 10 seconds
```

#### 2. Database Failure
```bash
# 1. Restore from latest backup
gunzip < /backups/laos/laos_20240501_020000.sql.gz | psql laos_production

# 2. Run migrations to ensure consistency
alembic upgrade head

# 3. Restart backend services
docker compose restart backend
```

#### 3. Redis Cache Loss
```bash
# Redis is cache-only (not critical)
# Just restart the service
docker compose restart redis
# Cache will be rebuilt on next access
```

#### 4. Complete Data Center Failure
```bash
# 1. Provision new infrastructure (VMs, networking)
# 2. Restore PostgreSQL from backup
# 3. Restore Redis cache (optional, can rebuild)
# 4. Deploy LAOS containers
# 5. Verify via health check
bash scripts/health-check.sh
```

### Backup Verification

Test backups monthly:
```bash
# 1. Create test database
createdb laos_test

# 2. Restore from backup
gunzip < /backups/laos/laos_20240501_020000.sql.gz | psql laos_test

# 3. Verify schema
psql laos_test -c "\d"

# 4. Check data integrity
psql laos_test -c "SELECT COUNT(*) FROM judgments;"

# 5. Cleanup
dropdb laos_test
```

## Security Hardening

### Access Control

**Firewall Rules:**
```bash
# Allow only necessary ports
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw default deny incoming
ufw default allow outgoing
ufw enable
```

**API Authentication:**
- All endpoints require JWT token (except login, health)
- Tokens expire in 30 minutes
- Refresh tokens valid for 7 days
- Force re-authentication for sensitive operations

### Secrets Management

**Never commit secrets to Git!**

Secrets in `.env` (not version controlled):
```
SECRET_KEY=<random-256-bit-hex>
DATABASE_PASSWORD=<strong-password>
OPENAI_API_KEY=<from-openai-dashboard>
JWT_SECRET=<random-256-bit-hex>
```

Generate secrets:
```bash
openssl rand -hex 32
```

### SQL Injection Prevention

Using Pydantic + SQLAlchemy prevents SQL injection:

```python
# ✅ SAFE: Parameterized query
stmt = select(User).where(User.email == email)
user = session.execute(stmt).scalar()

# ❌ UNSAFE: String interpolation (never do this!)
stmt = select(User).where(f"email = '{email}'")
```

### CSRF Protection

Enabled by default in FastAPI:
```python
from fastapi.middleware.csrf import CSRFMiddleware

app.add_middleware(
    CSRFMiddleware,
    secret_key=settings.SECRET_KEY,
    trusted_origins=settings.CORS_ALLOWED_ORIGINS
)
```

### CORS Configuration

File: `.env`
```
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Rollback Procedures

### Quick Rollback (Same Version)
```bash
# Stop all services
docker compose down

# Restart from previous state
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Rollback to Previous Version

```bash
# 1. Tag current version
docker tag myregistry/laos-backend:latest myregistry/laos-backend:v1.1.0-stable

# 2. Pull previous version
docker pull myregistry/laos-backend:v1.0.5

# 3. Update docker-compose to use old version
# Edit docker-compose.prod.yml:
#   image: myregistry/laos-backend:v1.0.5

# 4. Restart services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 5. If database migration needed, rollback:
alembic downgrade -1

# 6. Verify health
bash scripts/health-check.sh
```

### Data Rollback

If data was corrupted:
```bash
# Restore entire database from backup
dropdb laos_production
createdb laos_production
gunzip < /backups/laos/laos_20240501_020000.sql.gz | psql laos_production

# Restart services
docker compose restart backend
```

## Maintenance Windows

### Zero-Downtime Updates

Using rolling deployment:
```bash
# 1. Pull new images
docker pull myregistry/laos-backend:latest

# 2. Update one replica at a time
for i in 1 2 3; do
  docker compose up -d --no-deps --build backend
  sleep 30  # Wait for replica to be ready
  # Run smoke tests
  curl https://yourdomain.com/api/v1/health
done

# 3. Update frontend similarly
docker pull myregistry/laos-frontend:latest
docker compose up -d frontend
sleep 10
```

### Database Migrations During Maintenance

```bash
# 1. Schedule maintenance window
# 2. Notify users (email, banner)
# 3. Put application in maintenance mode
# 4. Stop new background jobs
# 5. Run migrations
alembic upgrade head
# 6. Test queries
psql laos_production -c "SELECT COUNT(*) FROM judgments;"
# 7. Bring application back online
```

## Common Operations

### Adding a New Superadmin User
```bash
docker compose exec backend python scripts/create_superadmin.py \
  --email admin@example.com \
  --password "TemporaryPassword123!"
```

### Export Audit Logs
```bash
docker compose exec postgres pg_dump \
  -U laos_app \
  laos_production \
  -t audit_logs \
  --no-privileges \
  > audit_export_$(date +%Y%m%d).sql
```

### Clear Cache
```bash
docker compose exec redis redis-cli FLUSHDB
```

### View Active Database Connections
```bash
docker compose exec postgres psql -U laos_app laos_production -c \
  "SELECT count(*) FROM pg_stat_activity WHERE datname='laos_production';"
```

## Compliance & Auditing

### Data Access Audit Trail
All document access is logged:
```sql
SELECT user_id, action, document_id, timestamp
FROM audit_logs
WHERE action IN ('VIEW', 'EXPORT', 'DOWNLOAD')
ORDER BY timestamp DESC
LIMIT 100;
```

### User Activity Report
```sql
SELECT 
  u.email,
  COUNT(a.id) as total_actions,
  MAX(a.created_at) as last_activity
FROM users u
LEFT JOIN audit_logs a ON u.id = a.user_id
GROUP BY u.email
ORDER BY last_activity DESC;
```

### Compliance Certification
Generate quarterly compliance report:
```bash
# Judgment completeness
SELECT 
  COUNT(*) as total_judgments,
  COUNT(CASE WHEN status = 'APPROVED' THEN 1 END) as approved,
  COUNT(CASE WHEN status = 'PENDING_REVIEW' THEN 1 END) as pending
FROM judgments
WHERE created_at > NOW() - INTERVAL '3 months';

# Action plan execution
SELECT 
  COUNT(*) as total_actions,
  COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed,
  ROUND(100.0 * COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) / COUNT(*), 2) as completion_rate
FROM action_items
WHERE created_at > NOW() - INTERVAL '3 months';
```

## Getting Help

- **Deployment Issues**: Check logs with `docker compose logs`
- **Database Problems**: See PostgreSQL logs at `/var/log/postgresql/`
- **SSL/TLS Issues**: Check certificate validity: `openssl s_client -connect yourdomain.com:443`
- **Performance Issues**: Monitor metrics in Prometheus dashboard
- **Security Concerns**: Contact security team immediately

---

**Last Updated**: May 1, 2024
**Maintained by**: DevOps Team
