# Docker Deployment Quickstart

Fast setup guide for deploying LAOS using Docker Compose in development, staging, or production.

## 5-Minute Local Setup

**For developers** - Get LAOS running on your machine in 5 minutes.

### Prerequisites
- Docker (19.03+) and Docker Compose (1.29+)
- 4GB RAM minimum, 20GB free disk space
- Git

### Setup

```bash
# 1. Clone repository (1 min)
git clone <repository-url>
cd laos

# 2. Copy development config (1 min)
cp .env.development .env

# 3. Build and start services (2 min)
docker compose up --build

# 4. Access application (1 min)
# Frontend:  http://localhost:3000
# API Docs:  http://localhost:8000/docs
# Logs:      docker compose logs -f
```

**Done!** All services ready. Code changes auto-reload.

### First Steps

1. **Frontend**: Open http://localhost:3000
2. **Login**: Use credentials from `.env.development`
3. **Upload Test Document**: Go to Judgments → Upload
4. **Review**: See extraction in real-time

### Stopping Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (clears database)
docker compose down -v

# Restart just backend
docker compose restart backend
```

---

## Staging Deployment

**For testing** before production - deploy to a staging server.

### Prerequisites
- Linux server (Ubuntu 20.04 LTS recommended)
- Docker and Docker Compose installed
- Domain name or IP address
- SSL certificate (optional)
- 8GB RAM, 50GB storage

### Staging Setup

```bash
# 1. SSH into server
ssh user@staging.yourdomain.com

# 2. Clone repository
cd /opt
sudo git clone <repository-url> laos
cd laos

# 3. Create production env
sudo cp .env.staging .env

# 4. Edit configuration
sudo nano .env
# Update:
# - DATABASE_URL=postgresql://...
# - REDIS_URL=redis://...
# - OPENAI_API_KEY=...
# - ALLOWED_HOSTS=staging.yourdomain.com

# 5. Start services
sudo docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 6. Verify
curl http://staging.yourdomain.com/api/v1/health
```

### Staging Configuration

**In `.env.staging`:**
```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json

# Database
DATABASE_URL=postgresql://laos:password@db-staging.company.com:5432/laos_staging

# Redis
REDIS_URL=redis://redis-staging.company.com:6379/0

# External Services
OPENAI_API_KEY=sk-...  # From staging account
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@company.com
SMTP_PASSWORD=...

# Security
SECRET_KEY=<random-256-bit-hex>
JWT_SECRET=<random-256-bit-hex>
CORS_ALLOWED_ORIGINS=https://staging.yourdomain.com

# Features
MAX_UPLOAD_SIZE_MB=100
ENABLE_STAGING_FEATURES=true
```

### Verify Staging

```bash
# Health check
curl https://staging.yourdomain.com/api/v1/health

# Check logs
docker compose logs -f backend

# Load test (light)
ab -n 100 -c 10 https://staging.yourdomain.com/api/v1/health

# Test user creation
docker compose exec backend python scripts/create_superadmin.py \
  --email staging@company.com \
  --password TempPass123!
```

---

## Production Deployment

**For live** - Deploy to production servers with high availability.

### Prerequisites
- **Infrastructure**:
  - Linux servers (Ubuntu 20.04 LTS) - 3+ for HA
  - Load balancer (AWS ELB, HAProxy, nginx)
  - PostgreSQL 16 (managed service recommended)
  - Redis 7 (cluster or sentinel)
  - S3 or object storage for documents
  - SSL certificate (Let's Encrypt or purchased)

- **Services Account**:
  - OpenAI API key (production account)
  - AWS/Cloud credentials
  - SMTP email service
  - DNS control

- **Team**:
  - DevOps engineer for deployment
  - DBA for database setup
  - System administrator for security

### Pre-Deployment Checklist

- [ ] All tests pass: `pytest && npm test`
- [ ] Code review completed
- [ ] Security scan passed
- [ ] Database migrations tested on staging
- [ ] Load test completed (expected traffic)
- [ ] Backup strategy configured
- [ ] Monitoring set up
- [ ] Runbooks documented
- [ ] Team trained on procedures

### Production Deployment Steps

#### Step 1: Prepare Infrastructure

```bash
# On primary server
sudo useradd -m laos
sudo usermod -aG docker laos
cd /var/www/laos

# Create required directories
sudo mkdir -p /var/log/laos
sudo mkdir -p /var/backups/laos
sudo chmod 755 /var/log/laos /var/backups/laos
```

#### Step 2: Setup Secrets

```bash
# Generate strong secrets
openssl rand -hex 32  # For SECRET_KEY
openssl rand -hex 32  # For JWT_SECRET

# Create secure .env file (NOT version controlled)
sudo nano /var/www/laos/.env

# Should contain:
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database (managed PostgreSQL)
DATABASE_URL=postgresql://laos_prod:password@db.production.aws.com:5432/laos_production

# Redis (cluster or sentinel)
REDIS_URL=redis://redis.production.aws.com:6379/0
REDIS_PASSWORD=...

# Secrets
SECRET_KEY=<generated-above>
JWT_SECRET=<generated-above>

# External Services
OPENAI_API_KEY=sk-...  # Production key
SMTP_HOST=email-smtp.us-east-1.amazonaws.com  # AWS SES or similar
SMTP_USERNAME=...
SMTP_PASSWORD=...

# Security
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# File Storage
STORAGE_TYPE=s3
S3_BUCKET=laos-documents-prod
S3_REGION=ap-south-1

# Email
ADMIN_EMAIL=admin@yourdomain.com
SUPPORT_EMAIL=support@yourdomain.com

# Set permissions
sudo chmod 600 /var/www/laos/.env
sudo chown laos:laos /var/www/laos/.env
```

#### Step 3: Deploy Application

```bash
# Clone repository
cd /var/www/laos
sudo git clone <repository-url> .
sudo chown -R laos:laos .

# Pull Docker images
docker pull registry.company.com/laos-backend:v1.0.0
docker pull registry.company.com/laos-frontend:v1.0.0
docker pull registry.company.com/laos-worker:v1.0.0

# Update docker-compose to use specific versions
sudo nano docker-compose.prod.yml
# Set image: registry.company.com/laos-backend:v1.0.0
```

#### Step 4: Start Services

```bash
# Create systemd service
sudo cat > /etc/systemd/system/laos.service << EOF
[Unit]
Description=LAOS Application Stack
Requires=docker.service
After=docker.service

[Service]
Type=simple
User=laos
WorkingDirectory=/var/www/laos
ExecStart=/usr/bin/docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
ExecStop=/usr/bin/docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable laos
sudo systemctl start laos

# Check status
sudo systemctl status laos
```

#### Step 5: Configure Reverse Proxy

```bash
# Nginx configuration
sudo nano /etc/nginx/sites-available/laos

# See example in docs/nginx.conf
# Configure SSL, rate limiting, compression
```

#### Step 6: Setup Backups

```bash
# Automated daily backups
sudo nano /usr/local/bin/backup-laos-db.sh

# See example in docs/DEPLOYMENT.md

# Add cron job
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-laos-db.sh
```

#### Step 7: Verify Deployment

```bash
# Health check
curl https://yourdomain.com/api/v1/health

# Check logs
docker compose logs -f backend | head -20

# Create test user
docker compose exec backend python scripts/create_superadmin.py \
  --email admin@yourdomain.com \
  --password <secure-password>

# Test login
curl -X POST https://yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@yourdomain.com","password":"<secure-password>"}'
```

### Monitoring Production

```bash
# Tail logs from all services
docker compose logs -f

# Monitor specific service
docker compose logs -f backend --tail=100

# Check resource usage
docker stats

# Monitor database
docker compose exec postgres psql -U laos -d laos_production -c \
  "SELECT datname, sum(heap_blks_read) as heap_read, sum(heap_blks_hit) as heap_hit \
  FROM pg_statio_user_tables GROUP BY datname;"
```

---

## Scaling Production Deployment

### Multiple Replicas

**Scale backend to 3 instances:**

```yaml
# docker-compose.prod.yml
services:
  backend:
    build: ./backend
    deploy:
      replicas: 3
    environment:
      - WORKERS=4
  
  frontend:
    build: ./frontend
    deploy:
      replicas: 2
```

**Restart with new replica count:**
```bash
docker compose up -d
docker compose ps  # Verify running
```

### Database High Availability

**PostgreSQL Replication:**
```bash
# Primary server setup
sudo pg_basebackup -h primary.db.com -U replication_user \
  -v -P -W -D /var/lib/postgresql/12/main -R

# Standby recovery.conf configured automatically
# Streaming replication configured
```

**Failover to Replica:**
```bash
# If primary fails, promote standby:
pg_ctl promote -D /var/lib/postgresql/12/main

# Update DNS/connection string
# Clients automatically reconnect
```

### Redis Cluster

**Setup 3-node Redis cluster:**
```bash
# Node 1
redis-server --port 7000 --cluster-enabled yes --cluster-config-file nodes.conf

# Node 2
redis-server --port 7001 --cluster-enabled yes --cluster-config-file nodes.conf

# Node 3
redis-server --port 7002 --cluster-enabled yes --cluster-config-file nodes.conf

# Create cluster
redis-cli --cluster create 127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002
```

---

## Common Operations

### Rolling Update

Deploy new version with zero downtime:

```bash
# 1. Pull new images
docker pull registry/laos-backend:v1.1.0

# 2. Update image in docker-compose.yml
sed -i 's/v1.0.0/v1.1.0/g' docker-compose.prod.yml

# 3. Recreate service (rolling restart)
docker compose up -d backend

# 4. Verify new version
curl https://yourdomain.com/api/v1/health | grep version

# 5. Check backend logs
docker compose logs -f backend --tail=50
```

### Database Migration

During scheduled maintenance:

```bash
# 1. Notify users (maintenance window)
# 2. Stop background workers (no new tasks)
docker compose exec backend celery -A app.worker control shutdown

# 3. Run migrations
docker compose exec backend alembic upgrade head

# 4. Verify schema
docker compose exec postgres psql -U laos_app laos_production -c "\d"

# 5. Restart workers
docker compose restart worker

# 6. Verify application
curl https://yourdomain.com/api/v1/health
```

### Rollback

If deployment has issues:

```bash
# 1. Revert to previous version
sed -i 's/v1.1.0/v1.0.0/g' docker-compose.prod.yml

# 2. Restart services
docker compose up -d

# 3. Verify health
curl https://yourdomain.com/api/v1/health

# 4. If database schema changed, rollback migration
docker compose exec backend alembic downgrade -1
```

### Clear Cache

If data gets stale:

```bash
# Clear all Redis cache
docker compose exec redis redis-cli FLUSHDB

# Clear specific key
docker compose exec redis redis-cli DEL user:123:documents

# View cache stats
docker compose exec redis redis-cli INFO stats
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check Docker daemon
sudo systemctl status docker

# Check resource limits
docker stats

# View docker logs
docker compose logs backend

# Rebuild images
docker compose build --no-cache
docker compose up -d
```

### High Memory Usage

```bash
# Check container memory
docker stats

# Limit container memory
# Edit docker-compose.prod.yml:
# services:
#   backend:
#     deploy:
#       resources:
#         limits:
#           memory: 1G

# Restart
docker compose up -d
```

### Database Connection Fails

```bash
# Test connection
docker compose exec backend python -c \
  "from app.db.session import get_db; print('Connected!')"

# Check DATABASE_URL
docker compose exec backend echo $DATABASE_URL

# View postgres logs
docker compose logs postgres

# Verify database exists
docker compose exec postgres psql -U laos -l
```

### Slow API Response

```bash
# Check if CPU-bound (workers)
docker stats

# Profile slow endpoint
docker compose logs backend | grep "duration"

# Scale up backend replicas
# Edit docker-compose.prod.yml and increase replicas

# Check database query performance
docker compose exec postgres psql -U laos -d laos_production \
  -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 5;"
```

---

## Security Best Practices

✅ **Do:**
- Use strong secrets (256-bit random)
- Enable HTTPS/TLS
- Rotate secrets regularly
- Use environment variables for secrets
- Keep Docker images updated
- Monitor logs for suspicious activity
- Backup database regularly
- Run security scans on images

❌ **Don't:**
- Commit `.env` file to Git
- Use weak passwords
- Run containers as root
- Expose ports unnecessarily
- Skip security updates
- Ignore error logs
- Mix development and production configs

---

## Getting Help

- **Deployment issues**: Check `docker compose logs`
- **Database problems**: See DEPLOYMENT.md database section
- **Performance issues**: Review monitoring section
- **Security concerns**: Contact security team immediately

---

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [LAOS README](README.md)
- [LAOS Deployment Guide](docs/DEPLOYMENT.md)
- [LAOS Architecture](docs/ARCHITECTURE.md)

---

**Last Updated**: May 1, 2024
**Status**: Production Ready
- Environment variables configured

## Local Development Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd laos
```

### 2. Configure Environment
```bash
cp .env.development .env
# Edit .env if needed for local customization
```

### 3. Build and Start Services
```bash
docker compose up --build
```

Services will start in this order:
1. PostgreSQL database (health check)
2. Redis cache (health check)
3. Backend API (depends on DB, Redis)
4. Worker (depends on DB, Redis)
5. Frontend UI (depends on Backend)
6. Nginx proxy (depends on all)

### 4. Access Services
- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/api/v1/health

### 5. View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f frontend
```

### 6. Database Management
```bash
# Connect to database
docker compose exec postgres psql -U laos -d laos

# Run migrations
docker compose exec backend /app/entrypoint.sh

# View database
\dt  # tables
\d table_name  # table schema
```

### 7. Stop Services
```bash
docker compose down
```

## Production Deployment

### 1. Prepare Server
```bash
# SSH to production server
ssh user@production-server

# Install Docker and Docker Compose
# Instructions: https://docs.docker.com/engine/install/
```

### 2. Clone and Configure
```bash
git clone <repository-url>
cd laos

# Create production environment
cp .env.example .env.production
# Edit .env.production with production values:
# - DATABASE_URL pointing to managed PostgreSQL service
# - REDIS_URL pointing to managed Redis service
# - SECRET_KEY and JWT_SECRET_KEY (32+ chars, random)
# - CORS_ALLOWED_ORIGINS for your domain
# - SENTRY_DSN for error tracking (optional)
```

### 3. Configure SSL Certificates
```bash
# Create SSL directory
mkdir -p ssl

# Place your SSL certificate and key:
# ssl/cert.pem - Your SSL certificate
# ssl/key.pem - Your private key

# Or generate self-signed (not for production):
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes
```

### 4. Deploy Application
```bash
# Copy .env.production to .env
cp .env.production .env

# Start services with production configuration
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify services
docker compose ps

# Check logs for errors
docker compose logs -f
```

### 5. Run Database Migrations
```bash
# If using Docker-managed database
docker compose exec backend /app/entrypoint.sh

# Or if using external database
export DATABASE_URL="postgresql://user:pass@host/laos"
docker run --rm -e DATABASE_URL laos-backend alembic upgrade head
```

### 6. Verify Deployment
```bash
# Check service health
curl http://localhost:8000/api/v1/health

# Check frontend
curl http://localhost:80/health

# View running containers
docker compose ps

# Check resource usage
docker stats
```

## Scaling in Production

### Increase Backend Replicas
```bash
# Edit docker-compose.prod.yml
# Change:
# backend:
#   deploy:
#     replicas: 5  # Increase from 3

docker compose up -d --scale backend=5
```

### Increase Worker Replicas
```bash
# For processing more async tasks
docker compose up -d --scale worker=4  # Increase from 2
```

## Monitoring and Maintenance

### View Logs
```bash
# All services
docker compose logs -f

# By level
docker compose logs -f --since 10m  # Last 10 minutes

# Specific service and number of lines
docker compose logs --tail 100 backend
```

### Health Checks
```bash
# Manual health verification
docker compose exec postgres pg_isready -U laos
docker compose exec redis redis-cli ping
curl http://localhost:8000/api/v1/health
```

### Backup Database
```bash
# Backup PostgreSQL
docker compose exec postgres pg_dump -U laos laos > backup.sql

# Backup Redis
docker compose exec redis redis-cli BGSAVE
docker cp $(docker compose ps -q redis):/data/dump.rdb ./redis-backup.rdb
```

### Restore Database
```bash
# Restore PostgreSQL
docker compose exec -T postgres psql -U laos laos < backup.sql

# Restore Redis
docker cp ./redis-backup.rdb $(docker compose ps -q redis):/data/dump.rdb
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker compose logs <service-name>

# Common issues:
# - Port already in use: docker compose down && docker compose up
# - Out of memory: Check docker resources
# - Network issues: docker compose down && docker network prune
```

### Database Connection Error
```bash
# Test connectivity
docker compose exec backend curl -f http://localhost:8000/api/v1/health

# Check database status
docker compose ps postgres
docker compose logs postgres

# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL
```

### High Memory Usage
```bash
# Check container stats
docker stats

# Reduce replicas
docker compose down && docker compose up -d

# Increase server resources
```

### SSL Certificate Issues
```bash
# Verify certificates
openssl x509 -in ssl/cert.pem -text -noout

# Check expiration
openssl x509 -enddate -noout -in ssl/cert.pem

# Update with new certificates and restart
docker compose down && docker compose up -d
```

## Security Notes

1. **Never commit secrets**: Use `.env.production` locally, inject in CI/CD
2. **Rotate credentials**: Change `SECRET_KEY` and `JWT_SECRET_KEY` regularly
3. **Backup data**: Regular PostgreSQL and Redis backups
4. **Monitor logs**: Watch for errors, security issues in logs
5. **Update images**: Regularly rebuild with latest OS/library patches
6. **Limit access**: Use firewall rules, VPN for server access
7. **SSL/TLS**: Always use HTTPS in production

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Production Checklist](https://docs.docker.com/develop/dev-best-practices/)
- [Security Best Practices](https://docs.docker.com/engine/security/)

## Support

For issues or questions:
1. Check logs: `docker compose logs -f <service>`
2. Review environment variables: `cat .env`
3. Check Docker disk space: `docker system df`
4. Consult documentation in `/docs` folder