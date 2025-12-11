# Docker Deployment Guide - Education System

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- 20GB free disk space

### Start All Services

```bash
# Clone the repository
git clone <repository-url>
cd Education-system

# Create environment file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f
```

### Access the Applications

- **Admin Portal**: http://localhost:3000
- **Teacher Portal**: http://localhost:3001
- **Student Portal**: http://localhost:3002
- **Django Admin**: http://localhost:8001/admin
- **FastAPI Docs**: http://localhost:8000/docs
- **Nginx Gateway**: http://localhost

---

## 📦 Service Architecture

### Services Overview

| Service | Port | Description | Technology |
|---------|------|-------------|------------|
| **db** | 5432 | PostgreSQL Database | PostgreSQL 15 |
| **backend-django** | 8001 | Main backend API | Django 4.2 + Python 3.11 |
| **backend-fastapi** | 8000 | Performance API | FastAPI + Python 3.11 |
| **frontend-admin** | 3000 | Admin micro frontend | Next.js 15 + TypeScript |
| **frontend-teacher** | 3001 | Teacher micro frontend | Next.js 15 + TypeScript |
| **frontend-student** | 3002 | Student micro frontend | Next.js 15 + TypeScript |
| **nginx** | 80, 443 | Reverse proxy & gateway | Nginx Alpine |

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
POSTGRES_DB=lms
POSTGRES_USER=postgres
POSTGRES_PASSWORD=SecurePassword123!

# Django Backend
DJANGO_SECRET_KEY=your-very-long-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com,backend-django,nginx

# FastAPI Backend
FASTAPI_SECRET_KEY=your-fastapi-secret-key-here

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost,http://yourdomain.com
```

### Generate Secret Keys

```bash
# Django Secret Key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# FastAPI Secret Key
openssl rand -hex 32
```

---

## 🔧 Docker Compose Commands

### Basic Operations

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart frontend-admin

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend-django

# Check service status
docker-compose ps

# Rebuild and restart
docker-compose up -d --build
```

### Scaling Services

```bash
# Scale frontend services
docker-compose up -d --scale frontend-admin=3 --scale frontend-teacher=2

# View scaled services
docker-compose ps
```

### Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes (WARNING: deletes data)
docker-compose down -v

# Remove unused Docker resources
docker system prune -a
```

---

## 🗄️ Database Management

### Initial Setup

```bash
# Run migrations
docker-compose exec backend-django python manage.py migrate

# Create superuser
docker-compose exec backend-django python manage.py createsuperuser

# Load initial data
docker-compose exec backend-django python manage.py loaddata initial_data.json
```

### Backup and Restore

```bash
# Backup database
docker-compose exec db pg_dump -U postgres lms > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U postgres lms

# Backup to Docker volume
docker run --rm -v education-system_db-data:/data -v $(pwd):/backup alpine tar czf /backup/db-backup.tar.gz /data

# Restore from Docker volume
docker run --rm -v education-system_db-data:/data -v $(pwd):/backup alpine tar xzf /backup/db-backup.tar.gz -C /
```

### Database Access

```bash
# Access PostgreSQL shell
docker-compose exec db psql -U postgres -d lms

# Run SQL query
docker-compose exec db psql -U postgres -d lms -c "SELECT * FROM users LIMIT 10;"

# Access via pgAdmin (add to docker-compose.yml)
# Then visit: http://localhost:5050
```

---

## 🔍 Monitoring & Debugging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service with tail
docker-compose logs -f --tail=100 backend-django

# Export logs
docker-compose logs > logs_$(date +%Y%m%d).txt
```

### Access Container Shell

```bash
# Django backend
docker-compose exec backend-django sh

# FastAPI backend
docker-compose exec backend-fastapi sh

# Database
docker-compose exec db sh

# Frontend
docker-compose exec frontend-admin sh
```

### Health Checks

```bash
# Check all services
docker-compose ps

# Check database
docker-compose exec db pg_isready -U postgres

# Check Django backend
curl http://localhost:8001/admin/

# Check FastAPI backend
curl http://localhost:8000/docs

# Check frontends
curl http://localhost:3000
curl http://localhost:3001
curl http://localhost:3002
```

### Resource Usage

```bash
# View resource usage
docker stats

# View disk usage
docker system df

# View specific container stats
docker stats education-frontend-admin
```

---

## 🐛 Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port
lsof -i :3000  # Linux/Mac
netstat -ano | findstr :3000  # Windows

# Stop conflicting service or change port in docker-compose.yml
```

#### Cannot Connect to Database

```bash
# Check if database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Wait for health check
docker-compose up -d db
docker-compose exec db pg_isready -U postgres

# Restart database service
docker-compose restart db
```

#### Frontend Build Fails

```bash
# Clear build cache
docker-compose build --no-cache frontend-admin

# Check logs during build
docker-compose build frontend-admin

# Build without Docker first to debug
cd frontend
bun install
bun run build
```

#### Backend Migration Issues

```bash
# Reset migrations (WARNING: deletes data)
docker-compose exec backend-django python manage.py migrate --fake-initial

# Force migration
docker-compose exec backend-django python manage.py migrate --run-syncdb

# Create new migration
docker-compose exec backend-django python manage.py makemigrations
```

#### Nginx Configuration Error

```bash
# Test Nginx configuration
docker-compose exec nginx nginx -t

# Reload Nginx configuration
docker-compose exec nginx nginx -s reload

# View Nginx logs
docker-compose logs nginx
```

---

## 🔐 Security Best Practices

### Production Deployment

1. **Change Default Passwords**
   ```env
   POSTGRES_PASSWORD=VerySecurePassword123!@#
   DJANGO_SECRET_KEY=long-random-string-min-50-chars
   ```

2. **Use HTTPS**
   - Place SSL certificates in `./nginx/ssl/`
   - Update nginx configuration for SSL

3. **Restrict Network Access**
   ```yaml
   # In docker-compose.yml, remove port mappings for internal services
   # Only expose nginx ports 80 and 443
   ```

4. **Enable Firewall**
   ```bash
   # Allow only necessary ports
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw enable
   ```

5. **Regular Updates**
   ```bash
   # Update images
   docker-compose pull
   docker-compose up -d
   ```

---

## 📊 Performance Optimization

### Production Configuration

```yaml
# docker-compose.prod.yml
services:
  backend-django:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8001 --workers 8 --timeout 120
```

### Caching

```yaml
# Add Redis to docker-compose.yml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  networks:
    - app-network
```

### Database Optimization

```bash
# Increase PostgreSQL performance
docker-compose exec db psql -U postgres -c "ALTER SYSTEM SET shared_buffers = '256MB';"
docker-compose exec db psql -U postgres -c "ALTER SYSTEM SET effective_cache_size = '1GB';"
docker-compose restart db
```

---

## 🚢 Deployment Strategies

### Single Server Deployment

```bash
# On production server
git clone <repo>
cd Education-system
cp .env.example .env
# Edit .env with production values
docker-compose up -d --build
```

### Multi-Server Deployment

Use Docker Swarm or Kubernetes for multi-server setups.

#### Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml education

# Scale services
docker service scale education_frontend-admin=3
```

### CI/CD Pipeline

Example GitHub Actions workflow:

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to server
        run: |
          ssh user@server 'cd /app && git pull && docker-compose up -d --build'
```

---

## 📝 Maintenance

### Regular Tasks

```bash
# Daily: Check service health
docker-compose ps

# Weekly: Backup database
./scripts/backup-database.sh

# Monthly: Update Docker images
docker-compose pull
docker-compose up -d

# Monthly: Clean unused resources
docker system prune -a
```

### Log Rotation

```bash
# Configure Docker log rotation
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

---

## 📞 Support

### Getting Help

1. Check logs: `docker-compose logs -f`
2. Review documentation: See `MICRO_FRONTEND_ARCHITECTURE.md`
3. Check service health: `docker-compose ps`
4. Verify configuration: Review `.env` file

### Useful Links

- Docker Documentation: https://docs.docker.com
- Docker Compose Reference: https://docs.docker.com/compose/compose-file/
- Next.js Deployment: https://nextjs.org/docs/deployment
- Django Deployment: https://docs.djangoproject.com/en/4.2/howto/deployment/
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/

---

## 🎉 Success!

If all services are running:

```bash
docker-compose ps
```

Should show all services as "Up" with healthy status.

Visit http://localhost to access the application through Nginx gateway!
