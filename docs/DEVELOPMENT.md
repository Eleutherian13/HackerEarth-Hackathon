# Developer Guide

Complete setup and development workflow for LAOS contributors.

## Local Development Setup

### Prerequisites
- **Python 3.11+** (for backend)
- **Node.js 20+** (for frontend)
- **PostgreSQL 16** (database)
- **Redis 7** (cache/messaging)
- **Docker & Docker Compose** (optional but recommended)
- **Git** (version control)

### Option 1: Docker Setup (Recommended)

Simplest and fastest for most developers:

```bash
# 1. Clone repository
git clone <repository-url>
cd laos

# 2. Use development environment
cp .env.development .env

# 3. Start all services
docker compose up --build

# 4. Verify setup
curl http://localhost:8000/api/v1/health
# Should return: {"status":"healthy",...}
```

**All services ready in 2-3 minutes.** Code changes live-reload automatically.

### Option 2: Local Machine Setup

For advanced developers or if Docker is unavailable:

#### 1. Backend Setup
```bash
cd backend

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create local .env
cp .env.example .env

# Edit .env with local database/Redis URLs
# DATABASE_URL=postgresql://laos:password@localhost:5432/laos
# REDIS_URL=redis://localhost:6379/0

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend server ready at http://localhost:8000

#### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Create .env.local (if needed for API override)
echo "VITE_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev

# Server ready at http://localhost:3000
```

Frontend server ready at http://localhost:3000

#### 3. PostgreSQL Setup
```bash
# Install PostgreSQL 16
# macOS: brew install postgresql@16
# Ubuntu: sudo apt install postgresql-16
# Windows: Download from postgresql.org

# Start PostgreSQL service
# macOS: brew services start postgresql@16
# Ubuntu: sudo systemctl start postgresql
# Windows: pgAdmin or Services

# Create database and user
createuser -s laos
createdb laos --owner laos

# Or with password:
psql -U postgres
CREATE USER laos WITH PASSWORD 'password';
CREATE DATABASE laos OWNER laos;
ALTER USER laos CREATEDB;
\q
```

#### 4. Redis Setup
```bash
# Install Redis
# macOS: brew install redis
# Ubuntu: sudo apt install redis-server
# Windows: Download from GitHub or use WSL

# Start Redis
# macOS: brew services start redis
# Ubuntu: sudo systemctl start redis-server
# Windows: redis-server.exe
```

### Verify Installation

```bash
# Backend health check
curl http://localhost:8000/api/v1/health

# Frontend accessibility
curl http://localhost:3000

# Database connection
psql -U laos -d laos -c "SELECT 1 as connection_test;"

# Redis connectivity
redis-cli ping
# Should return: PONG
```

## IDE Configuration

### VS Code Setup

#### Recommended Extensions
```json
{
  "extensions": {
    "python": "ms-python.python",
    "pylance": "ms-python.vscode-pylance",
    "black": "ms-python.black-formatter",
    "pylint": "ms-pylint.pylint",
    "fastapi": "ms-python.vscode-flask",
    "typescript": "esbenp.prettier-vscode",
    "eslint": "dbaeumer.vscode-eslint",
    "vueLS": "octref.vetur"
  }
}
```

#### VS Code Settings (.vscode/settings.json)
```json
{
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.eslint": "explicit"
    }
  },
  "python.linting.pylintEnabled": true,
  "python.linting.pylintArgs": ["--disable=W0212"],
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["backend/tests"],
  "editor.rulers": [88, 120],
  "files.exclude": {
    "**/__pycache__": true,
    "**/node_modules": true,
    "**/.pytest_cache": true
  }
}
```

#### Launch Configuration (.vscode/launch.json)
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI Backend",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
      "cwd": "${workspaceFolder}/backend",
      "justMyCode": true,
      "console": "integratedTerminal"
    },
    {
      "name": "Python: Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["backend/tests", "-v"],
      "cwd": "${workspaceFolder}",
      "justMyCode": true,
      "console": "integratedTerminal"
    }
  ]
}
```

### PyCharm / IntelliJ IDEA Setup

1. **Open Project**: File → Open → Select project root
2. **Configure Python Interpreter**:
   - Preferences → Project → Python Interpreter
   - Click gear → Add → Existing Environment
   - Select `backend/venv/bin/python`
3. **Configure Test Runner**:
   - Preferences → Tools → Python Integrated Tools
   - Test runner: pytest
   - Default test folder: backend/tests
4. **Code Style**:
   - Preferences → Editor → Code Style → Python
   - Hard wrap at: 88 (Black)
   - Enable "Optimize imports"

## Database Setup and Migrations

### Understanding Alembic

Database migrations are managed with Alembic, a lightweight SQL migration tool.

```
backend/alembic/
├── versions/          # Migration scripts
├── env.py            # Migration environment config
└── alembic.ini       # Alembic configuration
```

### Running Migrations

```bash
cd backend

# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision-hash>

# Rollback one migration
alembic downgrade -1

# View current database version
alembic current

# View migration history
alembic history
```

### Creating New Migrations

```bash
# Auto-generate migration based on model changes
alembic revision --autogenerate -m "Add new_column to users table"

# This creates a new file: backend/alembic/versions/000X_add_new_column.py
# Review the generated SQL before applying!

# Apply the migration
alembic upgrade head

# If needed, downgrade to redo
alembic downgrade -1
```

### Migration Best Practices

1. **Always Review Generated SQL**: Auto-generated migrations aren't always perfect
2. **Test on Local Database First**: Don't apply untested migrations to production
3. **Use Descriptive Names**: "add_user_status_column" not "update"
4. **Keep Migrations Small**: One logical change per migration
5. **Write Down Migrations**: Include `downgrade()` function for rollback capability
6. **Never Edit Applied Migrations**: Create new migrations instead

### Seeding Development Data

```bash
# Seed sample data
bash scripts/seed-db.sh

# This creates:
# - Departments (Law, Revenue, Home, Health, Education)
# - Users (superadmin, admin, reviewers, officers)
# - Sample documents (various processing stages)
# - Sample action plans
```

## Running Tests

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_admin_endpoints.py

# Run specific test function
pytest tests/unit/test_admin_endpoints.py::TestAdminEndpoints::test_list_users

# Run with coverage report
pytest --cov=app --cov-report=html

# Open coverage report: htmlcov/index.html
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm run test

# Run in watch mode (rerun on changes)
npm run test:watch

# Run with coverage
npm run test -- --coverage

# Run specific test
npm test -- DashboardPage.test.tsx
```

### Test Structure

**Backend** (`backend/tests/`):
- `unit/` - Unit tests (isolated components, no DB/API)
- `integration/` - Integration tests (with real services)
- `conftest.py` - Pytest configuration and fixtures
- `factories.py` - Test data factories
- `utils.py` - Test utilities (fake DB, mocks)

**Frontend** (`frontend/tests/`):
- Test files colocated with components: `Component.test.tsx`
- `setup.ts` - Vitest configuration

## Debugging Tips

### Backend Debugging

#### With VS Code
1. Set breakpoint (click left margin)
2. Press F5 or click Run → Debug (uses launch.json config)
3. Use Debug Console to inspect variables
4. Hover over variables to see values

#### With Print Statements
```python
# Simple approach for quick debugging
print(f"DEBUG: user_id={user_id}, score={score}")

# Or use logger (better for production code)
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Processing user {user_id}")
```

#### With REPL
```bash
# Drop into Python REPL within FastAPI context
python
>>> from app.db.session import get_db
>>> db = next(get_db())
>>> from app.models.domain.models import User
>>> user = db.query(User).first()
>>> print(user.email)
```

#### Common Issues

**Module Import Errors**
```bash
# Reinstall in development mode
cd backend
pip install -e .

# Or clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
```

**Database Connection Issues**
```bash
# Check PostgreSQL is running
psql -U laos -d laos -c "SELECT 1"

# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Reset database (loses all data)
dropdb laos && createdb laos --owner laos
alembic upgrade head
```

**Celery Worker Issues**
```bash
# Check Redis is running
redis-cli ping

# Inspect Celery queue
celery -A app.worker inspect active

# Clear stuck tasks
celery -A app.worker purge
```

### Frontend Debugging

#### React Developer Tools
1. Install [React Developer Tools](https://chrome.google.com/webstore/detail/react-developer-tools) extension
2. Press F12 → Components tab to inspect component tree
3. Right-click element → "Inspect component" to jump to source

#### Chrome DevTools
- F12 to open
- Sources tab for breakpoints
- Network tab to inspect API calls
- Console for JavaScript errors

#### Debugging API Calls
```typescript
// In component or service
console.log('Fetching user:', { id, endpoint });
const response = await fetch(`${API_URL}/users/${id}`);
console.log('Response:', response.status, await response.json());
```

## Code Style Guide

### Python (Backend)

#### Formatting
- **Formatter**: Black (88 character line length)
- **Import Sorting**: isort
- **Linting**: Pylint
- **Type Checking**: Mypy (optional in development)

```bash
# Auto-format code
black backend/app

# Sort imports
isort backend/app

# Lint for style issues
pylint backend/app

# Check types
mypy backend/app
```

#### Naming Conventions
```python
# Constants: ALL_CAPS
MAX_UPLOAD_SIZE_MB = 50
DEFAULT_PAGE_SIZE = 25

# Functions/methods: snake_case
def process_judgment(file_path: str) -> dict:
    pass

# Classes: PascalCase
class JudgmentExtractor:
    pass

# Private attributes: _leading_underscore
class User:
    def __init__(self):
        self._password_hash = None

# Constants within class: ALL_CAPS
class Config:
    API_VERSION = "1.0"
```

#### Type Hints (Required for Production Code)
```python
from typing import Optional, List
from pydantic import BaseModel

def extract_dates(text: str) -> List[str]:
    """Extract all dates from text.
    
    Args:
        text: Input text containing dates
        
    Returns:
        List of ISO format date strings
    """
    return []

class JudgmentDTO(BaseModel):
    case_number: str
    court_name: str
    judgment_date: Optional[str] = None
```

#### Docstring Style (Google Format)
```python
def calculate_confidence(extracted: dict, ground_truth: dict) -> float:
    """Calculate confidence score between extracted and actual data.
    
    Compares each field and returns weighted average confidence.
    Fields with higher importance get higher weights.
    
    Args:
        extracted: Dictionary of extracted field values
        ground_truth: Dictionary of actual field values
        
    Returns:
        Confidence score from 0.0 to 1.0
        
    Raises:
        ValueError: If inputs are None or invalid types
        
    Example:
        >>> score = calculate_confidence(
        ...     {"case_num": "2024-ABC-123"},
        ...     {"case_num": "2024-ABC-123"}
        ... )
        >>> score
        1.0
    """
```

### TypeScript (Frontend)

#### Formatting
- **Formatter**: Prettier
- **Linting**: ESLint
- **Type Checking**: Built-in (required)

```bash
# Auto-format
npx prettier --write src/

# Lint
npx eslint src/

# Type check
npm run check-types  # If configured
```

#### Naming Conventions
```typescript
// Constants: ALL_CAPS or camelCase
const MAX_RETRIES = 3;
const apiVersion = "1.0";

// Functions: camelCase
function processDocument(file: File): Promise<void> {}

// Components: PascalCase
function DashboardPage(): JSX.Element {}

// Types/Interfaces: PascalCase
interface User {
  id: string;
  email: string;
  role: UserRole;
}

// Enums: PascalCase
enum UserRole {
  ADMIN = "admin",
  REVIEWER = "reviewer",
  OFFICER = "officer"
}
```

#### JSDoc Comments
```typescript
/**
 * Fetches user by ID from API
 * 
 * @param userId - The user's unique identifier
 * @returns Promise resolving to User object
 * @throws Will throw if user not found (404)
 * 
 * @example
 * const user = await getUser('user123');
 * console.log(user.email);
 */
async function getUser(userId: string): Promise<User> {
  const response = await fetch(`/api/users/${userId}`);
  if (!response.ok) throw new Error('User not found');
  return response.json();
}
```

## Git Workflow

### Branch Naming
```
feature/add-user-management      # New feature
bugfix/fix-extraction-error      # Bug fix
docs/update-api-reference        # Documentation
chore/upgrade-dependencies       # Maintenance
```

### Commit Message Format
```
<type>: <subject>

<body>

<footer>

# Type: feat, fix, docs, style, refactor, test, chore
# Subject: imperative, present tense, no period
# Body: explain what and why, not how
# Footer: reference issues: Closes #123
```

#### Examples
```
feat: add document search functionality

Implement full-text search on judgment documents.
- Add search endpoint /api/documents/search
- Support filtering by date and department
- Index documents on upload for fast retrieval

Closes #456
```

```
fix: prevent extraction with very low confidence

Reject extraction attempts when confidence < 0.30 to avoid
hallucinated data being used for action plans.

Fixes #789
```

### Pull Request Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make Changes and Commit**
   ```bash
   git add .
   git commit -m "feat: describe your change"
   ```

3. **Push and Create PR**
   ```bash
   git push origin feature/your-feature
   # Then create PR on GitHub with description
   ```

4. **Code Review**
   - Address feedback promptly
   - Run tests locally: `pytest` and `npm test`
   - Update based on reviewer comments

5. **Merge and Cleanup**
   ```bash
   # After approval, merge via GitHub UI
   # Then cleanup local branch
   git checkout main
   git branch -d feature/your-feature
   ```

## Adding New Extraction Fields

### 1. Define Field in Data Model
File: `backend/app/models/domain/models.py`

```python
class JudgmentExtraction(Base):
    __tablename__ = "judgment_extractions"
    
    # ... existing fields ...
    
    # New field
    environmental_violation_details: str | None = Column(
        String,
        nullable=True,
        comment="Details of environmental violations mentioned in judgment"
    )
```

### 2. Create Database Migration
```bash
cd backend
alembic revision --autogenerate -m "Add environmental_violation_details field"
alembic upgrade head
```

### 3. Update Response Schema
File: `backend/app/models/schemas/extraction.py`

```python
class ExtractionDTO(BaseModel):
    """Extracted information from judgment document"""
    
    # ... existing fields ...
    
    environmental_violation_details: Optional[str] = Field(
        default=None,
        description="Details of environmental violations",
        json_schema_extra={"example": "Dumping of toxic waste without permission"}
    )
```

### 4. Update LLM Extraction Prompt
File: `backend/app/services/extraction/extractor.py`

```python
EXTRACTION_PROMPT = """
Extract the following fields from the judgment text:

{existing_fields}

5. Environmental violation details: If the judgment mentions any environmental 
   violations, describe them in detail. Include specific locations, substances, 
   and impacts mentioned.
   
Return as JSON with keys: {field_names}
"""
```

### 5. Add Unit Test
File: `backend/tests/unit/test_extraction.py`

```python
def test_extract_environmental_details():
    """Test extraction of environmental violation details"""
    text = """
    The court notes that the factory dumped 500 tons of toxic waste
    into the Yamuna River without authorization...
    """
    
    result = extractor.extract_fields(text)
    
    assert "environmental_violation_details" in result
    assert "Yamuna River" in result["environmental_violation_details"]
```

### 6. Update Frontend
File: `frontend/src/components/ExtractionReview.tsx`

```typescript
interface ExtractionData {
  // ... existing fields ...
  environmental_violation_details?: string;
}

function ExtractionReview({ data }: { data: ExtractionData }) {
  return (
    <div>
      {/* Existing fields */}
      
      {data.environmental_violation_details && (
        <TextField
          label="Environmental Violation Details"
          value={data.environmental_violation_details}
          multiline
          rows={4}
          fullWidth
        />
      )}
    </div>
  );
}
```

## Adding New Action Plan Types

### 1. Add Enum Value
File: `backend/app/models/enums.py`

```python
class ActionItemType(str, Enum):
    # Existing types
    MONETARY_FINE = "MONETARY_FINE"
    IMPLEMENTATION = "IMPLEMENTATION"
    
    # New type
    ENVIRONMENTAL_REMEDIATION = "ENVIRONMENTAL_REMEDIATION"
```

### 2. Create Plan Generator
File: `backend/app/services/action_plan/generator.py`

```python
def generate_environmental_remediation_plan(
    extraction: JudgmentExtraction
) -> ActionPlan:
    """Generate remediation action plan from environmental judgment"""
    
    items = []
    
    # Parse dates from extraction
    deadline = extraction.compliance_deadline
    
    items.append(ActionItem(
        type=ActionItemType.ENVIRONMENTAL_REMEDIATION,
        description=f"Remediate environmental violation: {extraction.environmental_violation_details}",
        deadline=deadline,
        responsible_department=extraction.court_location.split()[0]  # State department
    ))
    
    return ActionPlan(items=items)
```

### 3. Update Plan Selection Logic
File: `backend/app/services/action_plan/selector.py`

```python
def select_plan_generator(extraction: JudgmentExtraction) -> Callable:
    """Select appropriate plan generator based on extraction"""
    
    if extraction.environmental_violation_details:
        return generate_environmental_remediation_plan
    elif extraction.monetary_penalty:
        return generate_fine_payment_plan
    # ... other types ...
```

### 4. Add UI Component
File: `frontend/src/components/ActionPlanForm.tsx`

```typescript
const actionTypeOptions = [
  { value: ActionItemType.MONETARY_FINE, label: "Fine Payment" },
  { value: ActionItemType.ENVIRONMENTAL_REMEDIATION, label: "Environmental Remediation" },
  // ... others ...
];
```

## Performance Optimization

### Database Optimization
```bash
# Analyze slow queries
EXPLAIN ANALYZE SELECT * FROM judgments WHERE created_at > now() - '30 days'::interval;

# Create indexes on frequently filtered columns
CREATE INDEX idx_judgments_created_at ON judgments(created_at DESC);
CREATE INDEX idx_extractions_status ON judgment_extractions(status);
```

### API Response Optimization
- Use pagination: `?page=1&per_page=50`
- Implement field selection: `?fields=id,name` (if supported)
- Cache static data in Redis
- Compress responses with gzip

### Frontend Optimization
- Code splitting: `React.lazy()` for large pages
- Memoization: `useMemo`, `useCallback` for expensive computations
- Virtual scrolling for long lists
- Image optimization for PDF previews

## Useful Commands

```bash
# Format all code
black backend && npx prettier --write frontend

# Run all tests
pytest backend/tests && npm run test --prefix frontend

# Database operations
alembic upgrade head          # Apply migrations
alembic downgrade -1          # Rollback one migration
alembic history              # View migration history

# Check code quality
pylint backend/app --disable=W0212
npx eslint frontend/src

# Generate API docs
# Auto-generated at http://localhost:8000/docs

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Clean Docker
docker compose down -v   # Remove containers and volumes
docker system prune      # Clean unused images/networks
```

## Troubleshooting Development Issues

| Issue | Solution |
|-------|----------|
| Port 8000 already in use | `lsof -i :8000` then `kill -9 <PID>` |
| Module not found | `pip install -r requirements.txt` or `npm install` |
| Database connection error | Check PostgreSQL is running, verify DATABASE_URL |
| Redis connection error | Check Redis is running, verify REDIS_URL |
| CORS errors | Check CORS_ALLOWED_ORIGINS in .env |
| Migrations fail | Check for syntax errors in migration file, rollback: `alembic downgrade -1` |
| Tests fail | Run `pytest -v` to see detailed errors, check test dependencies |
| Docker compose fails | Rebuild: `docker compose up --build`, check Docker logs |

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Guide](https://docs.sqlalchemy.org/20/)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps

1. **Run setup**: `docker compose up --build`
2. **Create feature branch**: `git checkout -b feature/my-feature`
3. **Make changes**: Edit files and test locally
4. **Commit**: `git commit -m "feat: description"`
5. **Submit PR**: Push and create pull request on GitHub
6. **Get review**: Address reviewer comments
7. **Merge**: Merge via GitHub UI after approval

Happy coding! 🚀