# Education System - Complete Docker Deployment Guide

## 🚀 Quick Start

### One-Command Deployment

#### Windows (PowerShell)
```powershell
.\deploy.ps1
```

#### Linux/Mac
```bash
chmod +x deploy.sh
./deploy.sh
```

## 📋 Prerequisites

- **Docker Desktop** 20.10+ or **Docker Engine** 20.10+
- **Docker Compose** 2.0+
- **8GB RAM** minimum (16GB recommended)
- **20GB** free disk space

## 🏗️ System Architecture

```
Production Deployment Architecture
───────────────────────────────────

Internet
   │
   ▼
┌──────────────────────────────────────┐
│     Nginx Reverse Proxy              │
│     Port 80 (HTTP) / 443 (HTTPS)     │
└──────┬──────┬──────┬──────┬──────┬───┘
       │      │      │      │      │
   ┌───┴──┐ ┌─┴──┐ ┌─┴──┐ ┌─┴──┐ ┌─┴──┐
   │Django│ │Fast│ │Adm │ │Tea │ │Stu │
   │:8001 │ │API │ │in  │ │cher│ │dent│
   │      │ │8000│ │3000│ │3001│ │3002│
   └───┬──┘ └─┬──┘ └────┘ └────┘ └────┘
       │      │
       └──┬───┘
          ▼
    ┌─────────────┐
    │ PostgreSQL  │
    │   :5432     │
    │   (lms)     │
    └─────────────┘
```

## 🎯 Services Overview

| Service | Port | Description | Workers |
|---------|------|-------------|---------|
| **Nginx** | 80, 443 | Reverse proxy, SSL termination | - |
| **Django** | 8001 | Main backend, admin panel | 4 |
| **FastAPI** | 8000 | High-performance API, file uploads | 4 |
| **Frontend (Admin)** | 3000 | Admin dashboard (Next.js) | - |
| **Frontend (Teacher)** | 3001 | Teacher interface (Next.js) | - |
| **Frontend (Student)** | 3002 | Student interface (Next.js) | - |
| **PostgreSQL** | 5432 | Database (lms) | - |

## 📦 Installation Steps

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd Education-system
```

### Step 2: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use any text editor
```

### Step 3: Build Docker Images
```bash
# Build all images (takes 10-20 minutes first time)
docker-compose build

# Or build with no cache
docker-compose build --no-cache
```

### Step 4: Start Services
```bash
# Start all services in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f django
```

### Step 5: Initialize Database
```bash
# Run Django migrations
docker-compose exec django python manage.py migrate

# Create superuser (optional)
docker-compose exec django python manage.py createsuperuser

# Load initial data (if exists)
docker-compose exec django python manage.py loaddata initial_data.json
```

## 🔧 Environment Variables

### Required Variables (.env file)

```env
# ─────────────────────────────────
# Database Configuration
# ─────────────────────────────────
POSTGRES_DB=lms
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here

# ─────────────────────────────────
# Django Backend Configuration
# ─────────────────────────────────
DJANGO_SECRET_KEY=generate_with_django_command
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# ─────────────────────────────────
# FastAPI Backend Configuration
# ─────────────────────────────────
FASTAPI_SECRET_KEY=your_fastapi_secret_key_32_chars

# ─────────────────────────────────
# Frontend Configuration
# ─────────────────────────────────
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# ─────────────────────────────────
# CORS Configuration
# ─────────────────────────────────
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3002
```

### Generate Secret Keys

#### Django Secret Key
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

#### FastAPI Secret Key
```bash
openssl rand -hex 32
```

## 🌐 Accessing Services

### Development (Default Ports)

| Service | URL | Credentials |
|---------|-----|-------------|
| **Admin Dashboard** | http://localhost:3000 | admin / admin123 |
| **Teacher Portal** | http://localhost:3001 | 5GK3GY7 / gunay91 |
| **Student Portal** | http://localhost:3002 | 783QLRA / Humay2002 |
| **FastAPI Docs** | http://localhost:8000/docs | - |
| **Django Admin** | http://localhost:8001/admin | superuser created in step 5 |

### Production (Nginx Proxy)

| Service | URL |
|---------|-----|
| **Admin Dashboard** | https://yourdomain.com/admin |
| **Teacher Portal** | https://yourdomain.com/teacher |
| **Student Portal** | https://yourdomain.com/student |
| **API** | https://yourdomain.com/api |

## 🛠️ Common Operations

### View Service Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f django
docker-compose logs -f fastapi
docker-compose logs -f frontend-admin
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart django
```

### Stop Services
```bash
# Stop all (preserves data)
docker-compose stop

# Stop and remove containers (preserves data)
docker-compose down

# Stop and remove containers + volumes (DESTROYS DATA!)
docker-compose down -v
```

### Access Container Shell
```bash
# Django backend
docker-compose exec django sh

# FastAPI backend
docker-compose exec fastapi sh

# PostgreSQL
docker-compose exec postgres psql -U postgres -d lms
```

### Database Operations
```bash
# Create database backup
docker-compose exec postgres pg_dump -U postgres lms > backup_$(date +%Y%m%d).sql

# Restore database backup
docker-compose exec -T postgres psql -U postgres lms < backup_20250119.sql

# View database size
docker-compose exec postgres psql -U postgres -d lms -c "\l+"
```

## 🔒 SSL/HTTPS Configuration

### Step 1: Obtain SSL Certificates

#### Using Let's Encrypt (Recommended)
```bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d yourdomain.com
```

### Step 2: Copy Certificates
```bash
# Create SSL directory
mkdir -p nginx/ssl

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/
```

### Step 3: Update Nginx Configuration
Edit `nginx/conf.d/education-system-ssl.conf` and update domain names.

### Step 4: Restart Nginx
```bash
docker-compose restart nginx
```

## 📊 Monitoring & Health Checks

### Service Health
```bash
# Check all service health
docker-compose ps

# Check specific service health
docker-compose exec django python manage.py check
```

### Resource Usage
```bash
# View resource usage
docker stats

# View disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Check if port is already in use
netstat -tulpn | grep <port>

# Remove and recreate container
docker-compose rm <service-name>
docker-compose up -d <service-name>
```

### Database Connection Issues

```bash
# Test database connection
docker-compose exec postgres psql -U postgres -d lms -c "SELECT 1"

# Check database logs
docker-compose logs postgres

# Verify database credentials in .env
cat .env | grep POSTGRES
```

### Frontend Build Failures

```bash
# Clear Next.js cache
rm -rf frontend/.next frontend-teacher/.next frontend-student/.next

# Rebuild without cache
docker-compose build --no-cache frontend-admin

# Check Node.js memory
docker-compose build --build-arg NODE_OPTIONS="--max_old_space_size=4096" frontend-admin
```

### Performance Issues

```bash
# Increase worker count
# Edit docker-compose.yml and change worker numbers

# Increase container resources
# Edit Docker Desktop settings or add to docker-compose.yml:
services:
  django:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## 🚀 Production Deployment Checklist

- [ ] Generate and set strong secret keys in `.env`
- [ ] Set `DEBUG=False` in `.env`
- [ ] Update `ALLOWED_HOSTS` with production domain
- [ ] Update `CORS_ALLOWED_ORIGINS` with production URLs
- [ ] Obtain and configure SSL certificates
- [ ] Set up automated database backups
- [ ] Configure firewall to allow only ports 80, 443
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Set up log aggregation (ELK stack)
- [ ] Configure alerting for service failures
- [ ] Test disaster recovery procedures
- [ ] Document production architecture
- [ ] Set up CI/CD pipeline
- [ ] Configure automated security updates

## 📚 Additional Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Comprehensive deployment guide
- **[DOCKER_SETUP_COMPLETE.md](DOCKER_SETUP_COMPLETE.md)** - Quick reference
- **[BUG_FIX_AND_DOCKER_COMPLETE.md](BUG_FIX_AND_DOCKER_COMPLETE.md)** - Bug fixes and changes log

## 🆘 Support & Resources

### Useful Commands Reference

```bash
# Build and start
docker-compose up -d --build

# View all containers
docker ps -a

# Remove all stopped containers
docker container prune

# Remove all unused images
docker image prune -a

# View network info
docker network ls
docker network inspect education_education-network

# Export/Import images
docker save -o education-system.tar $(docker images -q education*)
docker load -i education-system.tar

# Execute Django management commands
docker-compose exec django python manage.py <command>

# Execute database queries
docker-compose exec postgres psql -U postgres -d lms -c "SELECT * FROM users LIMIT 5"
```

## 📝 License

[Your License Here]

## 👥 Contributing

[Contributing Guidelines]

---

**Last Updated:** October 19, 2025
**Docker Compose Version:** 3.8
**Minimum Docker Version:** 20.10+

**Status:** ✅ Production Ready
