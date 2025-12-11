# Education System Backend Services

## Architecture Overview

The backend consists of two main services:

### 1. FastAPI Service (Port 8000)
- **Main backend service** with comprehensive APIs
- Handles: Authentication, Students, Organizations, Academic Schedule, Evaluation System, etc.
- Location: `backend/app/`
- Start command: `python start_server.py`

### 2. Django Service (Port 8001) 
- **Teachers management service** built with Django REST Framework
- Handles: Teachers CRUD, Teacher statistics, Teacher filtering
- Location: `backend/django_backend/education_system/`
- Start command: `python manage.py runserver 8001`

## Prerequisites

1. **Python Environment**: Ensure you have Python 3.8+ installed
2. **PostgreSQL Database**: Database 'edu' running on localhost:5432
3. **Virtual Environment**: Recommended to use virtual environment

## Setup Instructions

### 1. Install Dependencies

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Install Django-specific dependencies
pip install django djangorestframework psycopg2-binary django-cors-headers python-decouple djangorestframework-simplejwt
```

### 2. Database Configuration

Both services connect to the same PostgreSQL database:
- **Host**: localhost
- **Port**: 5432
- **Database**: edu
- **Username**: postgres
- **Password**: 1111

### 3. Environment Variables

Create `.env` file in the backend directory with:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:1111@localhost:5432/edu
DB_HOST=localhost
DB_PORT=5432
DB_NAME=edu
DB_USER=postgres
DB_PASSWORD=1111

# Django Configuration
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True

# FastAPI Configuration
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8000
```

## Running the Services

### Option 1: Manual Startup (Recommended for Development)

**Terminal 1 - Start FastAPI Service (Port 8000):**
```bash
cd backend
python start_server.py
```

**Terminal 2 - Start Django Service (Port 8001):**
```bash
cd backend/django_backend/education_system
python manage.py runserver 8001
```

### Option 2: Using the Startup Script

```bash
cd backend
python run_all_services.py
```

### Option 3: Using Batch File (Windows)

```batch
start_all_services.bat
```

## Service Endpoints

### FastAPI Service (http://localhost:8000)
- **Authentication**: `/api/v1/auth/`
- **Users**: `/api/v1/users/`
- **Students**: `/api/v1/students/`
- **Organizations**: `/api/v1/organizations/`
- **Academic Schedule**: `/api/v1/academic-schedule/`
- **Evaluation System**: `/api/v1/evaluation/`
- **API Documentation**: `/docs`

### Django Service (http://localhost:8001)
- **Teachers List**: `/api/v1/teachers/`
- **Teacher Detail**: `/api/v1/teachers/{id}/`
- **Teacher Stats**: `/api/v1/teachers/stats/`
- **Filter Options**: `/api/v1/teachers/filter-options/`
- **Admin Panel**: `/admin/`

## Health Checks

### FastAPI Health Check:
```bash
curl http://localhost:8000/api/v1/health
```

### Django Health Check:
```bash
curl http://localhost:8001/api/v1/teachers/stats/
```

## Troubleshooting

### Common Issues:

1. **Port Conflicts**: 
   - Ensure ports 8000 and 8001 are not in use
   - Use `netstat -an | findstr ":8000"` to check port usage

2. **Database Connection**:
   - Verify PostgreSQL is running
   - Check database credentials in .env file
   - Test connection: `psql -U postgres -h localhost -d edu`

3. **Missing Dependencies**:
   - Reinstall requirements: `pip install -r requirements.txt`
   - Check Python version compatibility

4. **Django Migrations**:
   ```bash
   cd backend/django_backend/education_system
   python manage.py makemigrations
   python manage.py migrate
   ```

## Development Workflow

1. **Start both services** using the commands above
2. **FastAPI** handles most API operations
3. **Django** specifically handles teachers management
4. **Frontend** connects to both services:
   - Main features → FastAPI (port 8000)
   - Teachers page → Django (port 8001)

## Production Deployment

For production, consider:
1. Using a reverse proxy (nginx) to route requests
2. Consolidating services or using API Gateway
3. Implementing proper authentication across services
4. Using environment-specific configuration