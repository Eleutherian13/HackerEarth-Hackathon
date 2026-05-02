#!/bin/bash
set -e

# Docker configuration production deployment guide

# 1. Build and push images to registry
echo "Building and pushing Docker images..."
docker build -t laos-backend:latest ./backend
docker build -t laos-frontend:latest ./frontend
docker build -t laos-worker:latest -f worker/Dockerfile .

# 2. Tag for registry
REGISTRY=your-registry.azurecr.io
docker tag laos-backend:latest $REGISTRY/laos-backend:latest
docker tag laos-frontend:latest $REGISTRY/laos-frontend:latest
docker tag laos-worker:latest $REGISTRY/laos-worker:latest

# 3. Push to registry
docker push $REGISTRY/laos-backend:latest
docker push $REGISTRY/laos-frontend:latest
docker push $REGISTRY/laos-worker:latest

# 4. Deploy using production compose file
echo "Deploying services..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 5. Verify services are healthy
echo "Waiting for services to start..."
sleep 10
docker compose ps

# 6. Run database migrations
echo "Running database migrations..."
docker compose exec backend /app/entrypoint.sh

# 7. Setup SSL certificates (if needed)
# Place your SSL cert and key in ./ssl/cert.pem and ./ssl/key.pem

echo "Deployment completed!"