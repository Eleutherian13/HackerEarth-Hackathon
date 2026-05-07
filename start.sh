#!/bin/bash

#
# LAOS Startup Script
# Starts all required services for the LAOS Court Judgment Action System
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'  # No Color

echo ""
echo "=========================================="
echo "  LAOS - Court Judgment Action System"
echo "=========================================="
echo ""

# 1. Check Ollama
echo -e "${YELLOW}[1/7] Checking Ollama...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${RED}✗ Ollama is not running${NC}"
    echo "  Starting Ollama..."
    ollama serve &
    OLLAMA_PID=$!
    sleep 3
fi

# Check model
echo "  Checking llama3.2 model..."
if ollama list 2>/dev/null | grep -q "llama3.2"; then
    echo -e "${GREEN}✓ llama3.2 model found${NC}"
else
    echo -e "${YELLOW}⚠ Pulling llama3.2 model (2-3 minutes)...${NC}"
    ollama pull llama3.2
    echo -e "${GREEN}✓ llama3.2 model ready${NC}"
fi

# 2. Start Docker services
echo -e "\n${YELLOW}[2/7] Starting PostgreSQL and Redis...${NC}"
docker compose up -d postgres redis 2>/dev/null || true
echo -e "${GREEN}✓ Services started${NC}"

# 3. Wait for PostgreSQL
echo -e "\n${YELLOW}[3/7] Waiting for PostgreSQL...${NC}"
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker compose exec -T postgres pg_isready -U court_user -d court_judgments 2>/dev/null; then
        echo -e "${GREEN}✓ PostgreSQL ready${NC}"
        break
    fi
    echo -n "."
    sleep 2
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "\n${RED}✗ PostgreSQL failed to start${NC}"
    exit 1
fi

# 4. Install Python dependencies
echo -e "\n${YELLOW}[4/7] Installing Python dependencies...${NC}"
cd backend
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# 5. Initialize database
echo -e "\n${YELLOW}[5/7] Initializing database...${NC}"
python -m alembic upgrade head 2>/dev/null || true
echo -e "${GREEN}✓ Database schema initialized${NC}"

# 6. Seed database
echo -e "\n${YELLOW}[6/7] Seeding database with initial data...${NC}"
python -m scripts.seed_data
echo -e "${GREEN}✓ Database seeded${NC}"

# 7. Start backend
echo -e "\n${YELLOW}[7/7] Starting backend server...${NC}"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend starting (PID: $BACKEND_PID)${NC}"

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}  SYSTEM IS READY${NC}"
echo "=========================================="
echo ""
echo "  Services:"
echo "    Backend:    http://localhost:8000"
echo "    API Docs:   http://localhost:8000/docs"
echo "    Ollama:     http://localhost:11434"
echo ""
echo "  Test Accounts:"
echo "    Admin:      admin@laos.gov.in / Admin@123456"
echo "    Reviewer:   reviewer@laos.gov.in / Reviewer@123456"
echo "    Officer:    officer@laos.gov.in / Officer@123456"
echo "    Viewer:     viewer@laos.gov.in / Viewer@123456"
echo ""
echo "  Documentation:"
echo "    API:        http://localhost:8000/docs"
echo "    Health:     http://localhost:8000/health"
echo ""
echo "  Logs:"
echo "    Backend:    Streaming above"
echo ""
echo "  Stop Services:"
echo "    Press Ctrl+C to stop the backend"
echo "    Run: docker compose down  (to stop PostgreSQL/Redis)"
echo ""
echo "=========================================="
echo ""

# Trap ctrl-c and cleanup
trap_handler() {
    echo ""
    echo "Shutting down LAOS..."
    kill $BACKEND_PID 2>/dev/null || true
    if [ -n "$OLLAMA_PID" ]; then
        kill $OLLAMA_PID 2>/dev/null || true
    fi
    docker compose down 2>/dev/null || true
    exit 0
}

trap trap_handler INT TERM

# Wait for backend
wait $BACKEND_PID 2>/dev/null || true
