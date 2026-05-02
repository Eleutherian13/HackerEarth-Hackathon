# LAOS: Court Judgment Action System

A government compliance decision-support platform for reviewing judicial judgments and managing compliance action plans.

## Overview

**LAOS** (Court Judgment Action System) is an AI-powered document intelligence platform designed to help government departments:

1. **Extract** structured data from court judgments using LLM-powered OCR and NLP
2. **Verify** extracted information through human review workflows
3. **Plan** compliance actions with timeline tracking and accountability
4. **Monitor** action plan execution and generate compliance reports
5. **Audit** all system activities for transparency and accountability

### Key Features

- **Intelligent Document Processing**: Processes text-based and scanned PDFs with high accuracy
- **Human-in-the-Loop Verification**: Structured review workflow ensuring accuracy before implementation
- **Compliance Dashboard**: Real-time view of pending and completed compliance actions
- **Audit Trail**: Complete immutable record of all system activities
- **Multi-Department Support**: Role-based access control (Admin, Reviewer, Officer)
- **Scalable Architecture**: Kubernetes-ready with horizontal scaling for workers

## Quick Start (5 Minutes)

### Prerequisites
- Docker and Docker Compose (or local Python 3.11, Node 20, PostgreSQL 16, Redis 7)
- Git

### Local Development
```bash
# 1. Clone and setup (1 min)
git clone <repository-url>
cd laos
cp .env.development .env

# 2. Start services (2 min)
docker compose up --build

# 3. Access application (1 min)
# Frontend:  http://localhost:3000
# API Docs:  http://localhost:8000/docs
# Database: localhost:5432

# 4. Login with demo user (1 min)
# Email: reviewer1@example.com
# Password: Reviewer123!
```

All services will be ready in 2-3 minutes. Frontend and API are fully functional for testing.

**Note**: Database and seed data require migrations to run (happens automatically in first startup).

## Technology Stack

### Backend
- **Framework**: FastAPI (async Python)
- **Database**: PostgreSQL 16 (relational data, JSONB)
- **Cache/Messaging**: Redis 7 (caching, Celery broker)
- **Task Queue**: Celery (async PDF processing, AI extraction)
- **Document Processing**: 
  - Tesseract OCR (text extraction)
  - Poppler (PDF parsing)
  - PaddleOCR (layout analysis)
- **LLM Integration**: OpenAI GPT-4o-mini (field extraction)
- **ORM**: SQLAlchemy 2.0 (async)
- **Validation**: Pydantic v2 (runtime schema validation)

### Frontend
- **Framework**: React 18 (UI components)
- **Build Tool**: Vite (fast development/build)
- **Styling**: Material-UI (MUI) (component library)
- **Routing**: React Router v6 (client-side navigation)
- **Testing**: Vitest + React Testing Library
- **Server**: Nginx Alpine (production)

### Infrastructure
- **Containerization**: Docker / Docker Compose
- **Reverse Proxy**: Nginx (rate limiting, SSL termination)
- **Environment**: Supports local, staging, production
- **CI/CD**: Ready for GitHub Actions, GitLab CI

## Project Structure

```
laos/
├── backend/
│   ├── app/
│   │   ├── api/               # API routes
│   │   │   ├── v1/            # Version 1 endpoints
│   │   │   └── middleware/    # Auth, audit, rate limiting
│   │   ├── core/              # Config, security, logging
│   │   ├── models/
│   │   │   ├── domain/        # Database models
│   │   │   ├── enums.py       # Status enums
│   │   │   └── schemas/       # Request/response Pydantic schemas
│   │   ├── services/          # Business logic
│   │   │   ├── extraction/    # LLM-based field extraction
│   │   │   ├── action_plan/   # Action plan generation
│   │   │   └── dashboard/     # Analytics queries
│   │   ├── pipeline/          # Document processing pipeline
│   │   ├── db/                # Database setup, session management
│   │   ├── worker/            # Celery tasks
│   │   └── utils/             # Helpers, PDF processing
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Pytest suite
│   ├── Dockerfile             # Multi-stage production build
│   ├── entrypoint.sh          # Runs migrations + starts uvicorn
│   ├── requirements.txt       # Python dependencies
│   └── main.py                # FastAPI app initialization
│
├── frontend/
│   ├── src/
│   │   ├── components/        # Reusable React components
│   │   ├── pages/             # Page components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── services/          # API client code
│   │   ├── stores/            # State management
│   │   ├── types/             # TypeScript interfaces
│   │   ├── styles/            # Global styles
│   │   └── utils/             # Helper functions
│   ├── tests/                 # Vitest suite
│   ├── Dockerfile             # Multi-stage Node + Nginx build
│   ├── nginx.conf             # Nginx configuration
│   ├── vite.config.ts         # Vite configuration
│   ├── package.json           # NPM dependencies
│   └── tsconfig.json          # TypeScript configuration
│
├── worker/
│   ├── Dockerfile             # Celery worker container
│   ├── entrypoint.sh          # Worker startup
│   └── requirements.txt       # Python dependencies (shared with backend)
│
├── shared/
│   ├── constants/             # Shared constants
│   ├── schemas/               # Shared request/response schemas
│   └── types/                 # Shared TypeScript types
│
├── docker/
│   ├── nginx.conf             # Production reverse proxy
│   ├── postgres/              # PostgreSQL init scripts
│   ├── redis/                 # Redis configuration
│   └── README.md              # Docker setup guide
│
├── docs/
│   ├── DEVELOPMENT.md         # Developer setup and guide
│   ├── DEPLOYMENT.md          # Production deployment
│   ├── USER_GUIDE.md          # End-user documentation
│   ├── ARCHITECTURE.md        # System architecture details
│   ├── API.md                 # API reference (auto-generated from OpenAPI)
│   ├── PRODUCTION_CHECKLIST.md# Pre-launch verification
│   └── ADR/                   # Architecture Decision Records
│
├── scripts/
│   ├── setup-dev.sh           # Local development setup
│   ├── seed-db.sh             # Database seeding
│   ├── deploy-docker.sh       # Production deployment
│   ├── health-check.sh        # Health verification
│   └── generate-jwt-key.sh    # JWT secret generation
│
├── sample-data/
│   ├── judgments/             # Sample PDF files
│   ├── expected-outputs/      # Extraction ground truth
│   ├── scanned/               # Scanned PDF examples
│   ├── metadata.json          # Sample document metadata
│   └── README.md              # Data usage guide
│
├── docker-compose.yml         # Development services
├── docker-compose.prod.yml    # Production overrides
├── docker-compose.override.yml# Local development overrides
├── .env.example               # Environment variable template
├── .env.development           # Development defaults
├── .env.staging               # Staging configuration
├── DOCKER_QUICKSTART.md       # Docker deployment guide
└── Makefile                   # Common commands
```

## Core Concepts

### Document Processing Pipeline

```
PDF Upload
    ↓
[Validate] → Check MIME type, file size, integrity
    ↓
[Extract Text] → OCR (Tesseract/PaddleOCR) for scanned PDFs
    ↓
[Parse Structure] → Identify sections, orders, dates
    ↓
[Extract Fields] → Use LLM (GPT-4) to extract structured data
    ↓
[Confidence Scoring] → Assess extraction quality (0.0-1.0)
    ↓
[Human Review] → Reviewer verifies and corrects
    ↓
[Approval] → Lock for compliance planning
    ↓
[Action Plan] → Generate compliance actions with deadlines
    ↓
[Execution] → Track completion and compliance
    ↓
[Audit] → Immutable record of all changes
```

### Extraction Workflow

1. **Judgment Upload**: User uploads court judgment PDF
2. **Automated Extraction**: LLM extracts key information:
   - Case number, date, court
   - Litigant names
   - Key directions and deadlines
   - Action items for government
3. **Confidence Assessment**: System marks fields with confidence scores:
   - `HIGH` (>0.85): Likely correct, minimal review needed
   - `MEDIUM` (0.60-0.85): Review recommended
   - `LOW` (<0.60): Manual verification required
4. **Human Review**: Reviewer verifies, corrects, or rejects
5. **Approval**: Once verified, document locked for compliance planning

### Action Plan Management

1. **Auto-Generated**: Creates action items from extracted directions
2. **Deadline Tracking**: Tracks milestones and final dates
3. **Accountability**: Assigns to departments/officers
4. **Verification**: Allows document confirmation with evidence
5. **Reporting**: Dashboard shows status and compliance

## Key Workflows

### For Reviewers
1. Login to dashboard
2. See "Pending Review" documents
3. Review extracted fields (green = high confidence, yellow = medium, red = manual needed)
4. Correct any errors using inline editing
5. Approve or reject entire document
6. Document moves to "Action Planning" stage

### For Officers
1. Login to dashboard
2. See "Pending Actions" assigned to their department
3. View action items with deadlines
4. Upload completion documents as evidence
5. Mark actions as completed
6. Participate in audit trail

### For Admins
1. Manage users and permissions
2. View all documents across departments
3. Monitor system health (API, workers, database)
4. View audit logs
5. Generate compliance reports

## Authentication & Authorization

- **JWT Tokens**: Access tokens (30-min) + Refresh tokens (7-day)
- **Role-Based Access Control (RBAC)**:
  - `SUPERADMIN`: System administration
  - `ADMIN`: Department administration
  - `REVIEWER`: Document review and verification
  - `OFFICER`: Action item execution and completion
- **Rate Limiting**: 60 requests/min per IP, 100 per user
- **Session Timeout**: 30 minutes of inactivity

## Important Notes

### Confidence Thresholds
- `MIN_CONFIDENCE_THRESHOLD` (default 0.60): Below this requires manual review
- `HIGH_CONFIDENCE_THRESHOLD` (default 0.85): Above this is trusted for auto-actions
- These are configurable per environment

### Human Verification Requirements
**The system is designed with mandatory human verification before any compliance action is taken.** No extracted data is used for official action without explicit reviewer approval.

### Data Retention
- Extracted documents: Retained for 7 years (Indian compliance requirement)
- Audit logs: Retained indefinitely
- User sessions: Purged after 30 days of inactivity

## Documentation Structure

| Document | Purpose | Audience |
|----------|---------|----------|
| [README.md](README.md) | Project overview and quick start | Everyone |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Local setup, debugging, contribution | Developers |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment and operations | DevOps/Operators |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | How to use the system | End users |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and decisions | Architects |
| [docs/PRODUCTION_CHECKLIST.md](docs/PRODUCTION_CHECKLIST.md) | Pre-launch verification | Release managers |
| [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) | Docker deployment | DevOps/Developers |

## Getting Help

### For Development Issues
1. Check [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for setup issues
2. Review [docker/README.md](docker/README.md) for containerization
3. See individual service READMEs (backend/, frontend/, worker/)

### For Operations Issues
1. Check [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for deployment
2. Check [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) for deployment problems
3. Review logs: `docker compose logs -f <service>`
4. Run health check: `bash scripts/health-check.sh`

### For User Issues
1. See [docs/USER_GUIDE.md](docs/USER_GUIDE.md)
2. Check FAQ section
3. Review API documentation at `/docs` (Swagger UI)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Browsers                            │
│              (Reviewers, Officers, Admins)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│           Nginx Reverse Proxy (Port 80/443)                 │
│     (Rate Limiting, SSL Termination, Load Balancing)        │
├──────────────────────┬──────────────────────────────────────┤
│                      │
│  ┌────────────────────▼────────────────────┐
│  │     Frontend (Port 3000)                 │
│  │  React + Vite + MUI (in Nginx)          │
│  └────────────────────────────────────────┘
│
│  ┌────────────────────▼────────────────────┐  ┌──────────────┐
│  │  Backend API (Port 8000)                 │  │  PostgreSQL  │
│  │  FastAPI Async Application               │  │  (Port 5432) │
│  │  - Auth & RBAC                           │  │              │
│  │  - Document Management                   │  │  - Judgments │
│  │  - Extraction & Verification             │  │  - Reviews   │
│  │  - Action Planning                       │  │  - Audit Log │
│  │  - Analytics/Reports                     │  └──────────────┘
│  │  - Audit Logging                         │
│  └────────────────────────────────────────┘
│          │                         │
│          ├──────────────────────────┤
│          │                          │
│  ┌──────────────────┐     ┌─────────────────┐
│  │  Redis (Port 6379)│   │  Celery Workers  │
│  │  - Caching       │   │  - PDF Processing│
│  │  - Rate Limits   │   │  - Field Extract │
│  │  - Job Queue     │   │  - Action Plans  │
│  └──────────────────┘   └──────────────────┘
│
└──────────────────────────────────────────────────────────────┘
```

## Environment Configuration

The system supports three environments:

| Environment | DEBUG | LOG FORMAT | Use Case |
|-------------|-------|-----------|----------|
| **development** | true | text | Local development |
| **staging** | false | json | Pre-production testing |
| **production** | false | json | Live system |

See `.env.example` for all configurable options.

## Deployment Options

### Local Development
```bash
docker compose up
```
Perfect for local testing and debugging. Includes hot-reload.

### Staging/Production
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
Production-grade with multiple replicas, resource limits, and monitoring.

### Kubernetes (Future)
Charts and manifests ready for deployment to K8s clusters.

## Support & Contact

- **Documentation**: See `/docs` folder
- **API Reference**: Available at http://localhost:8000/docs (Swagger UI)
- **Issues**: Report in issue tracker with environment details
- **Security Issues**: Contact security team immediately (do not open public issues)

## License

[License info to be added]

## Acknowledgments

Built for government digital transformation initiative. Processes court judgments with accuracy and transparency.

---

**Last Updated**: May 2, 2026
**Status**: Production Ready ✓
### Key Features

- **Intelligent Document Processing**: Processes text-based and scanned PDFs with high accuracy
- **Human-in-the-Loop Verification**: Structured review workflow ensuring accuracy before implementation
- **Compliance Dashboard**: Real-time view of pending and completed compliance actions
- **Audit Trail**: Complete immutable record of all system activities
- **Multi-Department Support**: Role-based access control (Admin, Reviewer, Officer)
- **Scalable Architecture**: Kubernetes-ready with horizontal scaling for workers

## Quick Start (5 Minutes)

### Prerequisites
- Docker and Docker Compose (or local Python 3.11, Node 20, PostgreSQL 16, Redis 7)
- Git

### Local Development
```bash
# 1. Clone and setup (1 min)
git clone <repository-url>
cd laos
cp .env.development .env

# 2. Start services (2 min)
docker compose up --build

# 3. Access application (1 min)
# Frontend:  http://localhost:3000
# API Docs:  http://localhost:8000/docs
# Database: localhost:5432

# 4. Login with demo user (1 min)
# Email: reviewer1@example.com
# Password: Reviewer123!
```

All services will be ready in 2-3 minutes. Frontend and API are fully functional for testing.

**Note**: Database and seed data require migrations to run (happens automatically in first startup).

## Technology Stack

### Backend
- **Framework**: FastAPI (async Python)
- **Database**: PostgreSQL 16 (relational data, JSONB)
- **Cache/Messaging**: Redis 7 (caching, Celery broker)
- **Task Queue**: Celery (async PDF processing, AI extraction)
- **Document Processing**: 
  - Tesseract OCR (text extraction)
  - Poppler (PDF parsing)
  - PaddleOCR (layout analysis)
- **LLM Integration**: OpenAI GPT-4o-mini (field extraction)
- **ORM**: SQLAlchemy 2.0 (async)
- **Validation**: Pydantic v2 (runtime schema validation)

### Frontend
- **Framework**: React 18 (UI components)
- **Build Tool**: Vite (fast development/build)
- **Styling**: Material-UI (MUI) (component library)
- **Routing**: React Router v6 (client-side navigation)
- **Testing**: Vitest + React Testing Library
- **Server**: Nginx Alpine (production)

### Infrastructure
- **Containerization**: Docker / Docker Compose
- **Reverse Proxy**: Nginx (rate limiting, SSL termination)
- **Environment**: Supports local, staging, production
- **CI/CD**: Ready for GitHub Actions, GitLab CI

## Project Structure

```
laos/
├── backend/
│   ├── app/
│   │   ├── api/               # API routes
│   │   │   ├── v1/            # Version 1 endpoints
│   │   │   └── middleware/    # Auth, audit, rate limiting
│   │   ├── core/              # Config, security, logging
│   │   ├── models/
│   │   │   ├── domain/        # Database models
│   │   │   ├── enums.py       # Status enums
│   │   │   └── schemas/       # Request/response Pydantic schemas
│   │   ├── services/          # Business logic
│   │   │   ├── extraction/    # LLM-based field extraction
│   │   │   ├── action_plan/   # Action plan generation
│   │   │   └── dashboard/     # Analytics queries
│   │   ├── pipeline/          # Document processing pipeline
│   │   ├── db/                # Database setup, session management
│   │   ├── worker/            # Celery tasks
│   │   └── utils/             # Helpers, PDF processing
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Pytest suite
│   ├── Dockerfile             # Multi-stage production build
│   ├── entrypoint.sh          # Runs migrations + starts uvicorn
│   ├── requirements.txt       # Python dependencies
│   └── main.py                # FastAPI app initialization
│
├── frontend/
│   ├── src/
│   │   ├── components/        # Reusable React components
│   │   ├── pages/             # Page components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── services/          # API client code
│   │   ├── stores/            # State management
│   │   ├── types/             # TypeScript interfaces
│   │   ├── styles/            # Global styles
│   │   └── utils/             # Helper functions
│   ├── tests/                 # Vitest suite
│   ├── Dockerfile             # Multi-stage Node + Nginx build
│   ├── nginx.conf             # Nginx configuration
│   ├── vite.config.ts         # Vite configuration
│   ├── package.json           # NPM dependencies
│   └── tsconfig.json          # TypeScript configuration
│
├── worker/
│   ├── Dockerfile             # Celery worker container
│   ├── entrypoint.sh          # Worker startup
│   └── requirements.txt       # Python dependencies (shared with backend)
│
├── shared/
│   ├── constants/             # Shared constants
│   ├── schemas/               # Shared request/response schemas
│   └── types/                 # Shared TypeScript types
│
├── docker/
│   ├── nginx.conf             # Production reverse proxy
│   ├── postgres/              # PostgreSQL init scripts
│   ├── redis/                 # Redis configuration
│   └── README.md              # Docker setup guide
│
├── docs/
│   ├── DEVELOPMENT.md         # Developer setup and guide
│   ├── DEPLOYMENT.md          # Production deployment
│   ├── USER_GUIDE.md          # End-user documentation
│   ├── ARCHITECTURE.md        # System architecture details
│   ├── API.md                 # API reference (auto-generated from OpenAPI)
│   ├── PRODUCTION_CHECKLIST.md# Pre-launch verification
│   └── ADR/                   # Architecture Decision Records
│
├── scripts/
│   ├── setup-dev.sh           # Local development setup
│   ├── seed-db.sh             # Database seeding
│   ├── deploy-docker.sh       # Production deployment
│   ├── health-check.sh        # Health verification
│   └── generate-jwt-key.sh    # JWT secret generation
│
├── sample-data/
│   ├── judgments/             # Sample PDF files
│   ├── expected-outputs/      # Extraction ground truth
│   ├── scanned/               # Scanned PDF examples
│   ├── metadata.json          # Sample document metadata
│   └── README.md              # Data usage guide
│
├── docker-compose.yml         # Development services
├── docker-compose.prod.yml    # Production overrides
├── docker-compose.override.yml# Local development overrides
├── .env.example               # Environment variable template
├── .env.development           # Development defaults
├── .env.staging               # Staging configuration
├── DOCKER_QUICKSTART.md       # Docker deployment guide
└── Makefile                   # Common commands
```

## Core Concepts

### Document Processing Pipeline

```
PDF Upload
    ↓
[Validate] → Check MIME type, file size, integrity
    ↓
[Extract Text] → OCR (Tesseract/PaddleOCR) for scanned PDFs
    ↓
[Parse Structure] → Identify sections, orders, dates
    ↓
[Extract Fields] → Use LLM (GPT-4) to extract structured data
    ↓
[Confidence Scoring] → Assess extraction quality (0.0-1.0)
    ↓
[Human Review] → Reviewer verifies and corrects
    ↓
[Approval] → Lock for compliance planning
    ↓
[Action Plan] → Generate compliance actions with deadlines
    ↓
[Execution] → Track completion and compliance
    ↓
[Audit] → Immutable record of all changes
```

### Extraction Workflow

1. **Judgment Upload**: User uploads court judgment PDF
2. **Automated Extraction**: LLM extracts key information:
   - Case number, date, court
   - Litigant names
   - Key directions and deadlines
   - Action items for government
3. **Confidence Assessment**: System marks fields with confidence scores:
   - `HIGH` (>0.85): Likely correct, minimal review needed
   - `MEDIUM` (0.60-0.85): Review recommended
   - `LOW` (<0.60): Manual verification required
4. **Human Review**: Reviewer verifies, corrects, or rejects
5. **Approval**: Once verified, document locked for compliance planning

### Action Plan Management

1. **Auto-Generated**: Creates action items from extracted directions
2. **Deadline Tracking**: Tracks milestones and final dates
3. **Accountability**: Assigns to departments/officers
4. **Verification**: Allows document confirmation with evidence
5. **Reporting**: Dashboard shows status and compliance

## Key Workflows

### For Reviewers
1. Login to dashboard
2. See "Pending Review" documents
3. Review extracted fields (green = high confidence, yellow = medium, red = manual needed)
4. Correct any errors using inline editing
5. Approve or reject entire document
6. Document moves to "Action Planning" stage

### For Officers
1. Login to dashboard
2. See "Pending Actions" assigned to their department
3. View action items with deadlines
4. Upload completion documents as evidence
5. Mark actions as completed
6. Participate in audit trail

### For Admins
1. Manage users and permissions
2. View all documents across departments
3. Monitor system health (API, workers, database)
4. View audit logs
5. Generate compliance reports

## Authentication & Authorization

- **JWT Tokens**: Access tokens (30-min) + Refresh tokens (7-day)
- **Role-Based Access Control (RBAC)**:
  - `SUPERADMIN`: System administration
  - `ADMIN`: Department administration
  - `REVIEWER`: Document review and verification
  - `OFFICER`: Action item execution and completion
- **Rate Limiting**: 60 requests/min per IP, 100 per user
- **Session Timeout**: 30 minutes of inactivity

## Important Notes

### Confidence Thresholds
- `MIN_CONFIDENCE_THRESHOLD` (default 0.60): Below this requires manual review
- `HIGH_CONFIDENCE_THRESHOLD` (default 0.85): Above this is trusted for auto-actions
- These are configurable per environment

### Human Verification Requirements
**The system is designed with mandatory human verification before any compliance action is taken.** No extracted data is used for official action without explicit reviewer approval.

### Data Retention
- Extracted documents: Retained for 7 years (Indian compliance requirement)
- Audit logs: Retained indefinitely
- User sessions: Purged after 30 days of inactivity

## Documentation Structure

| Document | Purpose | Audience |
|----------|---------|----------|
| [README.md](README.md) | Project overview and quick start | Everyone |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Local setup, debugging, contribution | Developers |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment and operations | DevOps/Operators |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | How to use the system | End users |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and decisions | Architects |
| [docs/PRODUCTION_CHECKLIST.md](docs/PRODUCTION_CHECKLIST.md) | Pre-launch verification | Release managers |
| [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) | Docker deployment | DevOps/Developers |

## Getting Help

### For Development Issues
1. Check [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for setup issues
2. Review [docker/README.md](docker/README.md) for containerization
3. See individual service READMEs (backend/, frontend/, worker/)

### For Operations Issues
1. Check [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for deployment
2. Check [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) for deployment problems
3. Review logs: `docker compose logs -f <service>`
4. Run health check: `bash scripts/health-check.sh`

### For User Issues
1. See [docs/USER_GUIDE.md](docs/USER_GUIDE.md)
2. Check FAQ section
3. Review API documentation at `/docs` (Swagger UI)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Browsers                            │
│              (Reviewers, Officers, Admins)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│           Nginx Reverse Proxy (Port 80/443)                 │
│     (Rate Limiting, SSL Termination, Load Balancing)        │
├──────────────────────┬──────────────────────────────────────┤
│                      │
│  ┌────────────────────▼────────────────────┐
│  │     Frontend (Port 3000)                 │
│  │  React + Vite + MUI (in Nginx)          │
│  └────────────────────────────────────────┘
│
│  ┌────────────────────▼────────────────────┐  ┌──────────────┐
│  │  Backend API (Port 8000)                 │  │  PostgreSQL  │
│  │  FastAPI Async Application               │  │  (Port 5432) │
│  │  - Auth & RBAC                           │  │              │
│  │  - Document Management                   │  │  - Judgments │
│  │  - Extraction & Verification             │  │  - Reviews   │
│  │  - Action Planning                       │  │  - Audit Log │
│  │  - Analytics/Reports                     │  └──────────────┘
│  │  - Audit Logging                         │
│  └────────────────────────────────────────┘
│          │                         │
│          ├──────────────────────────┤
│          │                          │
│  ┌──────────────────┐     ┌─────────────────┐
│  │  Redis (Port 6379)│   │  Celery Workers  │
│  │  - Caching       │   │  - PDF Processing│
│  │  - Rate Limits   │   │  - Field Extract │
│  │  - Job Queue     │   │  - Action Plans  │
│  └──────────────────┘   └──────────────────┘
│
└──────────────────────────────────────────────────────────────┘
```

## Environment Configuration

The system supports three environments:

| Environment | DEBUG | LOG FORMAT | Use Case |
|-------------|-------|-----------|----------|
| **development** | true | text | Local development |
| **staging** | false | json | Pre-production testing |
| **production** | false | json | Live system |

See `.env.example` for all configurable options.

## Deployment Options

### Local Development
```bash
docker compose up
```
Perfect for local testing and debugging. Includes hot-reload.

### Staging/Production
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
Production-grade with multiple replicas, resource limits, and monitoring.

### Kubernetes (Future)
Charts and manifests ready for deployment to K8s clusters.

## Support & Contact

- **Documentation**: See `/docs` folder
- **API Reference**: Available at http://localhost:8000/docs (Swagger UI)
- **Issues**: Report in issue tracker with environment details
- **Security Issues**: Contact security team immediately (do not open public issues)

## License

[License info to be added]

## Acknowledgments

Built for government digital transformation initiative. Processes court judgments with accuracy and transparency.

---

**Last Updated**: May 2, 2026
**Status**: Production Ready ✓
