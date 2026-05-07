# LAOS System - Setup & Usage Guide

## ✅ Fixes Applied

### Backend Fixes

1. ✅ **Added JSON Login Endpoint** - New `/api/v1/auth/login-json` endpoint that accepts email/password as JSON (not form-data)
2. ✅ **Fixed CORS Configuration** - Updated `.env` to include `http://localhost:8080` for frontend communication
3. ✅ **Registered Missing Routers** - Added documents_extraction, dashboard_enhanced, and review routers to main.py
4. ✅ **Fixed Auth Schema** - Added `LoginRequest` schema for JSON-based authentication

### Frontend Fixes

1. ✅ **Fixed API Endpoints** - Changed from `/api/auth/` to `/api/v1/auth/` throughout
2. ✅ **Fixed Auth Interceptor** - Updated to use correct v1 endpoint for token refresh
3. ✅ **Added Route Protection** - Created `ProtectedRoute` component for auth-guarded routes
4. ✅ **Added Missing Routes** - Added Dashboard, Documents, and document detail routes to App.tsx
5. ✅ **Fixed Component Imports** - Updated pages to use axios client with auth headers
6. ✅ **Fixed Parameter Names** - ExtractionReview and ActionPlanReview now use correct route params
7. ✅ **Updated Navigation** - Header now includes Dashboard and Documents links

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (optional)

### Start the System

#### Option 1: Docker Compose (Recommended)

```bash
docker-compose up -d
```

This starts:

- PostgreSQL database (port 5432)
- Redis (port 6379)
- Backend API (port 8000)
- Frontend (port 8080)
- Nginx reverse proxy (port 80)

#### Option 2: Manual Start

**Terminal 1 - Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**

```bash
cd frontend
npm install
npm run dev
```

### Access the System

| Service     | URL                         | Type      |
| ----------- | --------------------------- | --------- |
| Frontend    | http://localhost:8080       | React App |
| Backend API | http://localhost:8000       | REST API  |
| API Docs    | http://localhost:8000/docs  | Swagger   |
| API ReDoc   | http://localhost:8000/redoc | ReDoc     |

## 🔐 Login Credentials

```
Email: admin@laos.gov.in
Password: Admin@123456
Role: Administrator

Email: reviewer@laos.gov.in
Password: Reviewer@123456
Role: Field Reviewer

Email: officer@laos.gov.in
Password: Officer@123456
Role: Compliance Officer

Email: viewer@laos.gov.in
Password: Viewer@123456
Role: System Viewer
```

## 📋 Workflow

1. **Login** (http://localhost:8080/login)
   - Use any of the credentials above
   - System stores auth tokens in localStorage
   - Auto-redirects to home on successful login

2. **Dashboard** (http://localhost:8080/dashboard)
   - View action plan metrics
   - See completion rates and priorities
   - Track overdue items

3. **Documents** (http://localhost:8080/documents)
   - View uploaded court judgment PDFs
   - Check processing status
   - Access document details

4. **Document Status** (http://localhost:8080/documents/:id/status)
   - Detailed document info
   - Trigger AI extraction
   - Monitor extraction progress

5. **Review Extractions** (http://localhost:8080/documents/:id/review)
   - Review AI-extracted fields
   - View confidence scores
   - Approve or edit fields
   - Add reviewer comments

6. **Action Plan** (http://localhost:8080/documents/:id/action-plan)
   - View generated action items
   - Assign responsibility
   - Set priorities and due dates
   - Mark items complete

## 🧪 Test the System

Run the integration test script:

```bash
python test_system.py
```

This will:

- ✓ Check backend health
- ✓ Test login endpoint
- ✓ Verify user authentication
- ✓ Test dashboard API
- ✓ Test documents API

## 🔑 Key Features Now Working

✅ **Authentication**

- Login with email/password
- JWT token management
- Token refresh on expiry
- Automatic redirect on unauthorized access

✅ **Frontend**

- Protected routes requiring authentication
- Navigation between pages
- API calls with auth headers
- Token stored in localStorage

✅ **Backend API**

- `/api/v1/auth/login-json` - JSON-based login
- `/api/v1/auth/refresh` - Token refresh
- `/api/v1/auth/logout` - Logout
- `/api/v1/auth/me` - Current user info
- `/api/v1/dashboard/summary` - Dashboard metrics
- `/api/v1/documents` - Document list
- `/api/v1/documents/{id}` - Document detail
- `/api/v1/documents/{id}/extract` - Trigger extraction
- `/api/v1/documents/{id}/action-plan` - Action items
- All other endpoints with proper auth

✅ **CORS**

- Frontend at :8080 can communicate with backend at :8000
- All required headers configured
- Credentials properly handled

## 🐛 Troubleshooting

### Backend not responding

```
Error: "Failed to load dashboard metrics"
Solution:
- Check backend is running on port 8000
- Verify CORS_ALLOWED_ORIGINS includes localhost:8080
- Check .env file is properly configured
```

### Login fails

```
Error: "invalid credentials"
Solution:
- Verify you're using correct email/password
- Check database is running and populated with test users
- Check backend logs for errors
```

### Frontend can't find routes

```
Error: "Cannot find module" or route not found
Solution:
- Run `npm install` in frontend directory
- Clear browser cache (Ctrl+Shift+Delete)
- Restart dev server (npm run dev)
```

### API endpoints return 401

```
Error: "Authorization failed"
Solution:
- Ensure auth token is stored in localStorage
- Check token hasn't expired
- Try logging out and logging back in
- Clear localStorage and refresh page
```

## 📝 Environment Configuration

### Backend (.env)

```
ENVIRONMENT=development
DATABASE_URL=postgresql://court_user:court_password@localhost:5432/court_judgments
REDIS_URL=redis://localhost:6379/0
CORS_ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
JWT_SECRET_KEY=dev-jwt-secret-key-minimum-32-characters-long-for-testing!
```

### Frontend (.env if needed)

```
VITE_API_URL=http://localhost:8000
```

## 🔗 API Documentation

Full API documentation available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📦 Project Structure

```
LAOS/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── auth.py      (Auth endpoints including login-json)
│   │   │   │   │   ├── documents.py
│   │   │   │   │   ├── dashboard.py
│   │   │   │   │   └── ...
│   │   │   ├── middleware/
│   │   │   │   └── auth.py          (CORS & Auth middleware)
│   │   ├── core/
│   │   │   ├── config.py            (Settings & CORS config)
│   │   │   └── security.py          (JWT & Auth logic)
│   │   ├── models/
│   │   │   ├── schemas/
│   │   │   │   └── auth.py          (LoginRequest schema)
│   │   │   └── domain/
│   │   │       └── models.py        (DB models)
│   │   └── services/
│   ├── main.py                      (App factory with routers)
│   ├── .env                         (Config with CORS_ALLOWED_ORIGINS)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx                  (Routes with ProtectedRoute)
│   │   ├── components/
│   │   │   ├── ProtectedRoute.tsx   (Auth guard)
│   │   │   └── laos/
│   │   │       └── Header.tsx       (Navigation with new links)
│   │   ├── lib/
│   │   │   ├── api-client.ts        (Axios with auth & refresh)
│   │   │   └── api-service.ts       (API methods using v1 paths)
│   │   └── pages/
│   │       ├── Login.tsx            (Uses authService.login)
│   │       ├── Dashboard.tsx        (Uses client for API)
│   │       ├── Documents.tsx        (Uses client for API)
│   │       ├── DocumentStatus.tsx
│   │       ├── ExtractionReview.tsx
│   │       └── ActionPlanReview.tsx
│   ├── vite.config.ts
│   └── package.json
├── test_system.py                   (Integration tests)
└── docker-compose.yml
```

## ✨ Next Steps

1. **Test the login flow** - Go to http://localhost:8080/login
2. **Explore dashboard** - View metrics and summaries
3. **Upload documents** - Add court judgment PDFs
4. **Review extractions** - Check AI-extracted fields
5. **Generate action plans** - Create compliance action items
6. **Monitor progress** - Track on dashboard

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. View backend logs: `docker logs backend` or terminal
3. Check frontend console: Browser DevTools → Console
4. Review API documentation: http://localhost:8000/docs
5. Check test results: `python test_system.py`

---

**Status**: ✅ All systems operational and integrated
**Last Updated**: 2024
**Version**: 1.0.0
