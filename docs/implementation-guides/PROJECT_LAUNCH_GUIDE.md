# 🚀 Education System - Complete Launch Guide

## Overview
This education system consists of three main components:
- **FastAPI Backend** (Port 8000) - Main API service
- **Django Backend** (Port 8001) - Teachers management service  
- **Next.js Frontend** (Port 3001) - React web application

## Prerequisites
- Python 3.8+ installed
- Node.js 18+ and Bun 1.0+ installed
- PostgreSQL 15+ running on port 5432
- Database 'edu' created with credentials: postgres/1111

## Quick Start

### Option 1: Automated Launch (Recommended)
```bash
# Start both backend services
cd backend
python run_all_services.py
# or
start_all_services.bat

# Start frontend (in new terminal)
cd frontend
bun dev
```

### Option 2: Manual Launch
```bash
# Terminal 1: FastAPI Service
cd backend
python start_server.py

# Terminal 2: Django Service
cd backend/django_backend/education_system
python manage.py runserver 8001

# Terminal 3: Frontend
cd frontend  
bun dev
```

## Service URLs
- 🌐 Frontend: http://localhost:3001
- 📡 FastAPI API: http://localhost:8000
- 📊 FastAPI Docs: http://localhost:8000/docs
- 🎓 Django API: http://localhost:8001
- 👥 Teachers Page: http://localhost:3001/teachers

## Backend Services Architecture

### FastAPI Service (Port 8000)
**Purpose**: Main API service handling core functionality
**Endpoints**:
- `/auth/*` - Authentication (login, register, JWT tokens)
- `/users/*` - User management
- `/students/*` - Student operations
- `/organizations/*` - Organization management
- `/academic-schedule/*` - Class schedules
- `/evaluation-system/*` - Grading and assessments
- `/requests/*` - Student requests
- `/student-orders/*` - Order management

### Django Service (Port 8001)
**Purpose**: Dedicated teachers management service
**Endpoints**:
- `/api/v1/teachers/` - List all teachers with pagination
- `/api/v1/teachers/{id}/` - Get specific teacher details
- `/api/v1/teachers/stats/` - Teachers statistics

## Database Structure
- **PostgreSQL Database**: `edu`
- **Tables**: 464 teachers across related tables
  - `teachers` - Teacher-specific data
  - `persons` - Personal information
  - `users` - Authentication data
  - `organizations` - School/department info
  - `dictionaries` - Reference data

## Development Features

### Frontend Components
- 📊 **Teachers Dashboard** - Complete data table with pagination
- 🔍 **Search & Filter** - Real-time teacher search
- 📈 **Statistics Cards** - Teacher counts and metrics
- 📱 **Responsive Design** - Mobile-first Tailwind CSS
- 🎨 **shadcn/ui Components** - Modern UI library

### API Features
- 🔐 **JWT Authentication** - Secure token-based auth
- 📄 **Auto Pagination** - Handle large datasets
- 🔍 **Search Filtering** - Query by name, email, department
- 📊 **Statistics Endpoints** - Data aggregation
- 🌐 **CORS Enabled** - Frontend integration

### Database Integration
- ✅ **Real Data** - 464 actual teachers from database
- 🔗 **Foreign Keys** - Proper relational structure
- 🏗️ **Django Models** - ORM with existing schema
- 📝 **Type Safety** - TypeScript interfaces matching API

## Testing & Validation

### API Testing
```bash
# Test FastAPI service
curl http://localhost:8000/docs

# Test Django teachers API
curl http://localhost:8001/api/v1/teachers/

# Test specific teacher
curl http://localhost:8001/api/v1/teachers/2610368562895842054/
```

### Frontend Testing
1. Navigate to http://localhost:3001/teachers
2. Verify teacher data loads
3. Test pagination and search
4. Check responsive design

## Troubleshooting

### Common Issues

**Port Conflicts**:
- FastAPI: Port 8000 (check with `netstat -an | findstr :8000`)
- Django: Port 8001 (check with `netstat -an | findstr :8001`)
- Frontend: Port 3001 (check with `netstat -an | findstr :3001`)

**Database Connection**:
```bash
# Test PostgreSQL connection
psql -U postgres -h localhost -d edu

# Check tables
\dt

# Verify teachers data
SELECT COUNT(*) FROM teachers;
```

**Service Status**:
- FastAPI Health: http://localhost:8000/docs
- Django Admin: http://localhost:8001/admin/
- Frontend Status: Check browser console for errors

### Error Resolution

**"Port already in use"**:
```bash
# Kill processes on port
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

**"Database connection failed"**:
- Verify PostgreSQL is running
- Check database credentials in config files
- Ensure 'edu' database exists

**"Frontend build errors"**:
```bash
cd frontend
bun install
bun run build
```

## Architecture Decisions

### Why Two Backend Services?
1. **Separation of Concerns**: FastAPI handles high-performance operations, Django manages teachers with admin interface
2. **Technology Strengths**: FastAPI for APIs, Django for ORM and admin
3. **Scalability**: Services can be scaled independently
4. **Maintainability**: Clear boundaries between functionalities

### Service Communication
- Frontend → FastAPI: Main app functionality
- Frontend → Django: Teachers management
- Both services → PostgreSQL: Shared database

## Development Workflow

### Adding New Features
1. **Database First**: Analyze existing schema
2. **Backend API**: Create endpoints with real data
3. **Frontend Integration**: Build UI with TypeScript
4. **Testing**: Validate with actual database

### Code Organization
```
backend/
├── app/                    # FastAPI service
├── django_backend/         # Django service
├── run_all_services.py     # Unified launcher
└── BACKEND_SERVICES_GUIDE.md

frontend/
├── src/app/teachers/       # Teachers page
├── src/types/             # TypeScript interfaces
├── src/lib/api/           # API clients
└── components/            # shadcn/ui components
```

### Best Practices
- ✅ Always use real database data
- ✅ Follow TypeScript strict mode
- ✅ Use shadcn/ui for consistency
- ✅ Implement proper error handling
- ✅ Test with actual API endpoints

## Production Deployment

### Environment Variables
```bash
# Backend
DATABASE_URL=postgresql://user:pass@host:5432/edu
JWT_SECRET=your-secure-secret
DEBUG=False

# Frontend  
NEXT_PUBLIC_API_URL=https://your-api-domain.com
NEXT_PUBLIC_DJANGO_API_URL=https://your-django-domain.com
```

### Docker Setup (Optional)
```dockerfile
# Consider containerization for production
# Separate containers for FastAPI, Django, Frontend
```

## Support & Resources

### Documentation
- FastAPI Docs: http://localhost:8000/docs
- Django Admin: http://localhost:8001/admin/
- API Endpoints: See BACKEND_SERVICES_GUIDE.md

### Key Files
- `backend/run_all_services.py` - Unified service launcher
- `backend/BACKEND_SERVICES_GUIDE.md` - Detailed backend guide
- `frontend/src/app/teachers/page.tsx` - Teachers page implementation
- `backend/django_backend/education_system/teachers/` - Django teachers app

---

🎓 **Education System** - Complete Full-Stack Application
Built with FastAPI, Django, Next.js, and PostgreSQL