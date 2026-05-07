# LAOS Quick Start Guide

Welcome to the LAOS Court Judgment Action System! This guide will help you get the system up and running in minutes.

## Prerequisites

- **Ollama:** Download from https://ollama.ai
- **Docker:** https://www.docker.com/products/docker-desktop
- **Node.js:** v18+ (for frontend)
- **Python:** 3.10+ (for backend)

## Option 1: Automated Start (Recommended)

The easiest way to start everything:

```bash
cd /path/to/LAOS
chmod +x start.sh
./start.sh
```

The script will:

1. ✓ Check/start Ollama
2. ✓ Pull llama3.2 model
3. ✓ Start PostgreSQL & Redis
4. ✓ Install dependencies
5. ✓ Initialize database
6. ✓ Seed test data
7. ✓ Start backend server

**Output:**

```
==========================================
  SYSTEM IS READY
==========================================

  Services:
    Backend:    http://localhost:8000
    API Docs:   http://localhost:8000/docs
    Ollama:     http://localhost:11434

  Test Accounts:
    Admin:      admin@laos.gov.in / Admin@123456
    Reviewer:   reviewer@laos.gov.in / Reviewer@123456
    Officer:    officer@laos.gov.in / Officer@123456
    Viewer:     viewer@laos.gov.in / Viewer@123456
```

## Option 2: Manual Start (Step-by-Step)

### Step 1: Start Ollama

```bash
# Start Ollama service
ollama serve

# In another terminal, pull the model
ollama pull llama3.2

# Verify connection
curl http://localhost:11434/api/tags
```

### Step 2: Start Docker Services

```bash
docker compose up -d postgres redis
```

### Step 3: Start Backend

```bash
cd backend
pip install -r requirements.txt
python -m alembic upgrade head
python -m scripts.seed_data
cd ..
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Step 4: Start Frontend

```bash
cd frontend
npm install
npm run dev
```

## Accessing the System

### Web Interface

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000

### API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Test Accounts (Login Credentials)

| Email                | Password        | Role               |
| -------------------- | --------------- | ------------------ |
| admin@laos.gov.in    | Admin@123456    | Administrator      |
| reviewer@laos.gov.in | Reviewer@123456 | Field Reviewer     |
| officer@laos.gov.in  | Officer@123456  | Compliance Officer |
| viewer@laos.gov.in   | Viewer@123456   | System Viewer      |

## Using the System

### 1. Upload a Document

1. Go to Home page (http://localhost:5173)
2. Click "Upload Document"
3. Select a PDF file (court judgment)
4. Click "Upload"

### 2. Extract Fields

1. Go to Documents page
2. Click on your uploaded document
3. Click "Extract" button
4. Wait for Ollama to process (30-60 seconds)

### 3. Review Extractions

1. Click "Review Extractions"
2. See fields extracted by AI on right panel
3. Check confidence scores (green >85%, yellow 70-85%, orange <70%)
4. For each field:
   - ✓ **Approve** if correct
   - ✏️ **Edit** if needs changes
   - ✗ **Reject** if incorrect
   - 🚩 **Flag** for manual review

### 4. Generate Action Plan

1. After approving/editing fields, click "Generate Action Plan"
2. System creates actionable items from verified fields

### 5. Review Action Items

1. Click "View Action Plan"
2. See all generated action items
3. Mark items complete as they're implemented
4. Track compliance deadlines

### 6. Monitor Dashboard

1. Go to Dashboard page
2. See real-time metrics:
   - Total actions
   - Completion rate
   - Critical items
   - Overdue items
   - Department breakdown

## System Workflow

```
PDF Upload
    ↓
[Extract] Using Ollama AI
    ↓
[Review] Human verification
    ↓
[Action Plan] Generate compliance items
    ↓
[Monitor] Track completion
    ↓
[Dashboard] Real-time metrics
```

## Troubleshooting

### Problem: "Ollama not available"

**Solution:**

```bash
# Start Ollama
ollama serve

# In another terminal
ollama pull llama3.2

# Wait 2-3 minutes for model download
```

### Problem: "Cannot connect to database"

**Solution:**

```bash
# Check Docker is running
docker ps

# Check PostgreSQL logs
docker compose logs postgres

# Restart services
docker compose restart postgres
```

### Problem: "Frontend not loading"

**Solution:**

```bash
cd frontend
npm install
npm run dev

# Check backend is running
curl http://localhost:8000/health
```

### Problem: "API returns 401 Unauthorized"

**Solution:**

1. Log out and log back in
2. Check token is stored in localStorage
3. Try incognito mode if cookies are cached

## Features Demonstration

### AI Extraction Demo

1. Upload a sample court judgment PDF
2. System extracts:
   - Case number
   - Court name
   - Judgment date
   - Operative directions
   - Appeal periods
   - Compliance deadlines

### Confidence Scoring

- Fields are extracted with confidence scores (0-1)
- **High confidence (>85%):** Usually correct, minor edits
- **Medium confidence (70-85%):** Review recommended
- **Low confidence (<70%):** Careful review needed

### Action Items

- **COMPLIANCE:** Implement court order within deadline
- **APPEAL:** Consider appeal within limitation period
- **INTERNAL_REVIEW:** Internal verification needed
- **ESCALATION:** Escalate to higher authority
- **MONITORING:** Track implementation progress

### Priority Calculation

- **CRITICAL:** Due within 7 days or marked urgent
- **HIGH:** Due within 30 days
- **MEDIUM:** Due within 90 days
- **LOW:** Due after 90 days

## Performance Expectations

| Operation          | Time     | Notes                 |
| ------------------ | -------- | --------------------- |
| PDF Upload         | <1s      | File storage          |
| Field Extraction   | 30-60s   | Depends on page count |
| Field Verification | Variable | Manual process        |
| Action Plan Gen    | 5-10s    | Rule-based processing |
| API Response       | <200ms   | Average response time |

## Database Reset

To clear all data and start fresh:

```bash
cd backend

# Drop all tables
python -m alembic downgrade base

# Recreate schema
python -m alembic upgrade head

# Reseed data
python -m scripts.seed_data
```

## Stopping the System

### If using start.sh:

```bash
# Press Ctrl+C in terminal
# Script automatically cleans up services
```

### If started manually:

```bash
# Stop backend: Ctrl+C
# Stop frontend: Ctrl+C in its terminal

# Stop Docker services:
docker compose down
```

## Next Steps

1. **Try the demo:** Upload a sample court judgment
2. **Review documentation:** See IMPLEMENTATION_COMPLETION.md
3. **Explore API:** Visit http://localhost:8000/docs
4. **Check logs:** Monitor backend output for issues

## Need Help?

- **API Documentation:** http://localhost:8000/docs
- **Project README:** See README.md in each directory
- **Logs:** Check backend console for detailed error messages
- **Database:** Connect with: `psql -U court_user -d court_judgments -h localhost`

## Success!

You now have a fully functional court judgment processing system with:

- ✓ AI-powered extraction
- ✓ Human verification workflow
- ✓ Intelligent action planning
- ✓ Real-time dashboard
- ✓ Complete audit trail

Happy judgment processing! 🎉
