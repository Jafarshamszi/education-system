# Education Management System - Backend

This is the FastAPI backend for the Education Management System.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Git

### Installation

1. **Clone and navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Run the setup script:**
   ```bash
   python setup.py
   ```

3. **Activate virtual environment:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

4. **Configure environment:**
   - Copy `.env.example` to `.env`
   - Update database credentials in `.env`

5. **Setup database:**
   ```bash
   # Create PostgreSQL database
   createdb education_system
   
   # Run migrations
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

6. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/               # API routes
│   │   └── api_v1/
│   │       ├── api.py     # Main API router
│   │       └── endpoints/ # Individual endpoint modules
│   ├── core/              # Core functionality
│   │   ├── config.py      # Settings and configuration
│   │   └── database.py    # Database connection
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── crud/              # Database operations
│   ├── services/          # Business logic
│   └── main.py            # FastAPI application
├── alembic/               # Database migrations
├── tests/                 # Test files
├── requirements.txt       # Dependencies
├── alembic.ini           # Alembic configuration
└── .env.example          # Environment template
```

## 🔧 Available Scripts

```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
python -m pytest

# Format code
python -m black app/
python -m isort app/

# Lint code
python -m flake8 app/

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
alembic downgrade -1
```

## 📊 API Documentation

Once the server is running, visit:

- **Swagger UI:** http://localhost:8000/api/v1/docs
- **ReDoc:** http://localhost:8000/api/v1/redoc
- **Health Check:** http://localhost:8000/health

## 🗄️ Database Schema

The system uses the existing education database schema with tables including:

- `accounts` - User authentication
- `persons` - Personal information
- `students` - Student records
- `teachers` - Staff records
- `academic_groups` - Class groups
- `courses` - Course information
- And many more...

## 🔐 Authentication

The API uses JWT tokens for authentication:

```bash
# Login
POST /api/v1/auth/login

# Register
POST /api/v1/auth/register

# Refresh token
POST /api/v1/auth/refresh
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app

# Run specific test file
python -m pytest tests/test_auth.py
```

## 🐳 Docker

```dockerfile
# Build image
docker build -t education-backend .

# Run container
docker run -p 8000:8000 education-backend
```

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT secret key | Required |
| `DEBUG` | Enable debug mode | False |
| `CORS_ORIGINS` | Allowed CORS origins | localhost:3000 |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run linting and tests
6. Submit a pull request