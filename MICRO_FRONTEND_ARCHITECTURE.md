# Micro Frontend Architecture - Education System

## Overview

This Education System follows a **Micro Frontend Architecture** with multiple independent frontend applications communicating with a unified backend system. This architecture provides:

- **Independent Development**: Each frontend can be developed, tested, and deployed independently
- **Technology Flexibility**: Each micro frontend can use different versions or technologies
- **Scalability**: Each frontend can be scaled independently based on load
- **Team Autonomy**: Different teams can work on different frontends without conflicts
- **Fault Isolation**: Issues in one frontend don't affect others

## Architecture Components

### 🎯 **Backend Services** (Single Unified Backend)

#### 1. **Django Backend** (`backend-django`)
- **Port**: 8001
- **Purpose**: Main application logic, admin interface, ORM models
- **Technologies**: Python 3.11, Django 4.2+, Django REST Framework
- **Responsibilities**:
  - User authentication & authorization
  - Database models & migrations
  - Admin panel
  - Static file management
  - Primary business logic

#### 2. **FastAPI Backend** (`backend-fastapi`)
- **Port**: 8000
- **Purpose**: High-performance API endpoints, file uploads, real-time features
- **Technologies**: Python 3.11, FastAPI 0.100+, Uvicorn
- **Responsibilities**:
  - File upload/download endpoints
  - Real-time WebSocket connections
  - Background task processing
  - Performance-critical operations

#### 3. **PostgreSQL Database** (`db`)
- **Port**: 5432
- **Database Name**: `lms`
- **Purpose**: Centralized data storage
- **Technologies**: PostgreSQL 15
- **Features**:
  - ACID compliance
  - Full relational database capabilities
  - Shared by both backend services

---

### 🖥️ **Micro Frontend Services** (Multiple Independent Frontends)

#### 1. **Admin Portal** (`frontend-admin`)
- **Port**: 3000
- **Purpose**: Administrative interface for system management
- **Technologies**: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui
- **Target Users**: System administrators, rectors
- **Features**:
  - Student group management
  - Class schedule management
  - Course management
  - Teacher assignments
  - Student enrollments
  - Organization management
  - System configuration

#### 2. **Teacher Portal** (`frontend-teacher`)
- **Port**: 3001
- **Purpose**: Interface for teachers to manage their classes
- **Technologies**: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui
- **Target Users**: Teachers, instructors
- **Features**:
  - Attendance marking
  - Grade entry
  - Course content management
  - Student list viewing
  - Schedule viewing
  - Assignment management

#### 3. **Student Portal** (`frontend-student`)
- **Port**: 3002
- **Purpose**: Interface for students to access their information
- **Technologies**: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui
- **Target Users**: Students
- **Features**:
  - Attendance viewing
  - Grade viewing
  - Course enrollment
  - Schedule viewing
  - Assignment submissions
  - Profile management

---

### 🔀 **API Gateway** (Nginx)

#### **Nginx Reverse Proxy** (`nginx`)
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Purpose**: Single entry point for all services, routing, SSL termination
- **Technologies**: Nginx stable-alpine
- **Responsibilities**:
  - Route requests to appropriate services
  - Load balancing
  - SSL/TLS termination
  - Static file serving
  - CORS handling
  - Request logging

**Routing Strategy:**
```
http://yourdomain.com/           → Frontend Admin (3000)
http://yourdomain.com/teacher/   → Frontend Teacher (3001)
http://yourdomain.com/student/   → Frontend Student (3002)
http://yourdomain.com/api/       → Backend APIs (8000/8001)
http://yourdomain.com/admin/     → Django Admin (8001)
```

---

## Service Communication

### Communication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                         Nginx Gateway                        │
│                      (Port 80/443)                           │
└─────┬────────────────┬────────────────┬─────────────────────┘
      │                │                │
      ▼                ▼                ▼
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Admin    │    │ Teacher  │    │ Student  │
│ Frontend │    │ Frontend │    │ Frontend │
│ (3000)   │    │ (3001)   │    │ (3002)   │
└────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │
     └───────────────┴───────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
    ┌──────────┐          ┌──────────┐
    │ Django   │          │ FastAPI  │
    │ Backend  │◄────────►│ Backend  │
    │ (8001)   │          │ (8000)   │
    └────┬─────┘          └────┬─────┘
         │                     │
         └──────────┬──────────┘
                    ▼
              ┌──────────┐
              │PostgreSQL│
              │ Database │
              │  (5432)  │
              └──────────┘
```

### Network Configuration

- **Network Name**: `app-network`
- **Driver**: bridge
- **Inter-service Communication**: All services can communicate via service names
- **Examples**:
  - Frontends connect to backends via: `http://backend-django:8001` or `http://backend-fastapi:8000`
  - Backends connect to database via: `postgresql://db:5432/lms`

---

## Deployment

### Docker Compose Commands

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d frontend-admin

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Remove all volumes (WARNING: Deletes data)
docker-compose down -v
```

### Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
POSTGRES_DB=lms
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# Django Configuration
DJANGO_SECRET_KEY=your_django_secret_key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# FastAPI Configuration
FASTAPI_SECRET_KEY=your_fastapi_secret_key

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3002,http://yourdomain.com
```

---

## Development vs Production

### Development Mode

```bash
# Run backends locally
cd backend
python manage.py runserver 0.0.0.0:8001  # Django
uvicorn main:app --reload --port 8000     # FastAPI

# Run frontends locally
cd frontend && bun dev              # Admin on 3000
cd frontend-teacher && bun dev      # Teacher on 3001
cd frontend-student && bun dev      # Student on 3002
```

### Production Mode (Docker)

```bash
# Build and start all services
docker-compose up -d --build

# Monitor logs
docker-compose logs -f

# Scale specific frontend
docker-compose up -d --scale frontend-admin=3
```

---

## Benefits of This Architecture

### ✅ **Independent Deployment**
- Deploy admin portal without affecting student/teacher portals
- Rollback individual frontends if issues occur
- Deploy updates during off-peak hours for specific user groups

### ✅ **Technology Flexibility**
- Upgrade Next.js version in one frontend without affecting others
- Experiment with new libraries in one portal
- Use different UI frameworks if needed

### ✅ **Team Autonomy**
- Frontend teams work independently
- Reduced merge conflicts
- Faster development cycles

### ✅ **Performance Optimization**
- Optimize student portal for mobile
- Add caching specific to teacher workflows
- Scale services independently based on load

### ✅ **Fault Isolation**
- Bug in admin portal doesn't crash student portal
- Performance issues isolated to specific service
- Easier debugging and monitoring

### ✅ **User Experience**
- Tailored UX for each user type
- Faster load times (smaller bundle sizes)
- Personalized features per portal

---

## Monitoring & Maintenance

### Health Checks

```bash
# Check service status
docker-compose ps

# Check database health
docker-compose exec db pg_isready -U postgres

# Check backend APIs
curl http://localhost:8001/health
curl http://localhost:8000/health

# Check frontend status
curl http://localhost:3000
curl http://localhost:3001
curl http://localhost:3002
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend-admin
docker-compose logs -f backend-django
docker-compose logs -f db

# Last 100 lines
docker-compose logs --tail=100
```

### Backups

```bash
# Backup database
docker-compose exec db pg_dump -U postgres lms > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U postgres lms

# Backup volumes
docker run --rm -v education-system_db-data:/data -v $(pwd):/backup alpine tar czf /backup/db-backup.tar.gz /data
```

---

## Security Considerations

### 🔒 **Network Isolation**
- All services communicate via internal network
- Only Nginx exposes ports to external world
- Database not accessible from outside

### 🔒 **Environment Variables**
- Sensitive data in `.env` file (not committed to git)
- Different secrets for each environment
- Rotate secrets regularly

### 🔒 **SSL/TLS**
- Nginx handles SSL termination
- Place certificates in `./nginx/ssl/`
- Internal communication can use HTTP (within Docker network)

### 🔒 **CORS Configuration**
- Strict CORS policies defined
- Only allowed origins can access APIs
- Different origins for each frontend

---

## Troubleshooting

### Common Issues

**Issue**: Frontend can't connect to backend
- **Solution**: Check `NEXT_PUBLIC_API_URL` environment variable
- **Solution**: Ensure backends are running: `docker-compose ps`

**Issue**: Database connection failed
- **Solution**: Wait for DB health check to pass
- **Solution**: Check database credentials in `.env`

**Issue**: Port already in use
- **Solution**: Stop conflicting service or change port in docker-compose.yml
- **Solution**: Use `docker-compose down` to clean up

**Issue**: Build fails
- **Solution**: Clear Docker cache: `docker-compose build --no-cache`
- **Solution**: Check Dockerfile syntax in each service

---

## Future Enhancements

### Potential Improvements

1. **Service Mesh**: Implement Istio or Linkerd for advanced routing
2. **Container Orchestration**: Move to Kubernetes for production scale
3. **CI/CD Pipeline**: Automated testing and deployment for each frontend
4. **Monitoring**: Add Prometheus + Grafana for metrics
5. **Logging**: Centralized logging with ELK stack
6. **Caching**: Redis for session management and caching
7. **CDN**: CloudFront or Cloudflare for static assets
8. **API Gateway**: Kong or AWS API Gateway for advanced features

---

## Conclusion

This micro frontend architecture provides:
- **Scalability**: Each service scales independently
- **Flexibility**: Technology choices per service
- **Reliability**: Fault isolation between services
- **Maintainability**: Clear service boundaries
- **Developer Experience**: Independent development and deployment

The architecture supports the Education System's need for different user interfaces while maintaining a unified backend and database.
