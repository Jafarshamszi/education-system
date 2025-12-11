# Education System - Docker Deployment Guide

## Quick Start (Development)

### Prerequisites
- Docker Desktop or Docker Engine (20.10+)
- Docker Compose (2.0+)
- 8GB RAM minimum
- 20GB free disk space

### Step 1: Clone and Setup

```bash
cd Education-system
cp .env.example .env
```

### Step 2: Configure Environment

Edit `.env` file and update:
- `POSTGRES_PASSWORD` - Change to a secure password
- `DJANGO_SECRET_KEY` - Generate using: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
- `FASTAPI_SECRET_KEY` - Any random 32+ character string

### Step 3: Build and Start Services

```bash
# Build all containers
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Step 4: Initialize Database

```bash
# Run Django migrations
docker-compose exec django python manage.py migrate

# Create Django superuser
docker-compose exec django python manage.py createsuperuser

# Load initial data (if any)
docker-compose exec django python manage.py loaddata initial_data.json
```

### Step 5: Access Applications

- **Admin Frontend**: http://localhost:3000 or http://admin.localhost
- **Teacher Frontend**: http://localhost:3001 or http://teacher.localhost
- **Student Frontend**: http://localhost:3002 or http://student.localhost
- **Django Admin**: http://localhost:8001/admin/
- **FastAPI Docs**: http://localhost:8000/docs
- **Nginx (All services)**: http://localhost

---

## Production Deployment

### Step 1: Server Setup

**Requirements:**
- Ubuntu 22.04 LTS or similar
- 4 CPU cores minimum
- 16GB RAM minimum
- 50GB SSD storage
- Docker and Docker Compose installed

### Step 2: Domain Configuration

Update `/etc/hosts` or configure DNS:
```
your-server-ip admin.yourdomain.com
your-server-ip teacher.yourdomain.com
your-server-ip student.yourdomain.com
your-server-ip api.yourdomain.com
```

### Step 3: Production Environment

Create `.env.production`:

```bash
# Database - CHANGE THESE!
POSTGRES_DB=edu_prod
POSTGRES_USER=edu_admin
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE

# Django
DJANGO_SECRET_KEY=GENERATE_STRONG_SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=admin.yourdomain.com,teacher.yourdomain.com,student.yourdomain.com,api.yourdomain.com
CORS_ALLOWED_ORIGINS=https://admin.yourdomain.com,https://teacher.yourdomain.com,https://student.yourdomain.com

# FastAPI
FASTAPI_SECRET_KEY=GENERATE_STRONG_SECRET_KEY

# Frontend
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
```

### Step 4: SSL/TLS Setup (Let's Encrypt)

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Stop nginx container temporarily
docker-compose stop nginx

# Generate certificates
sudo certbot certonly --standalone -d admin.yourdomain.com -d teacher.yourdomain.com -d student.yourdomain.com -d api.yourdomain.com

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/

# Update nginx configuration to use SSL (see nginx/conf.d/education-system-ssl.conf)

# Restart nginx
docker-compose start nginx
```

### Step 5: Deploy

```bash
# Build with production settings
docker-compose -f docker-compose.yml --env-file .env.production build

# Start services
docker-compose -f docker-compose.yml --env-file .env.production up -d

# Initialize database
docker-compose exec django python manage.py migrate
docker-compose exec django python manage.py collectstatic --noinput
docker-compose exec django python manage.py createsuperuser
```

---

## Service Management

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
# All services
docker-compose restart

# Specific service
docker-compose restart django
```

### Stop Services
```bash
docker-compose stop
```

### Remove Everything (CAUTION!)
```bash
docker-compose down -v  # This deletes volumes including database!
```

---

## Backup and Restore

### Backup Database
```bash
# Create backup
docker-compose exec postgres pg_dump -U postgres edu > backup_$(date +%Y%m%d_%H%M%S).sql

# Or with compression
docker-compose exec postgres pg_dump -U postgres edu | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore Database
```bash
# From SQL file
docker-compose exec -T postgres psql -U postgres edu < backup_file.sql

# From compressed file
gunzip < backup_file.sql.gz | docker-compose exec -T postgres psql -U postgres edu
```

### Backup Volumes
```bash
# Backup all volumes
docker run --rm -v education-system_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data_backup.tar.gz -C /data .
```

---

## Monitoring

### Check Container Health
```bash
docker-compose exec postgres pg_isready
docker-compose exec django python manage.py check
```

### Monitor Resource Usage
```bash
docker stats
```

### Database Connections
```bash
docker-compose exec postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs [service-name]

# Check if port is already in use
sudo netstat -tulpn | grep [port-number]
```

### Database Connection Issues
```bash
# Enter postgres container
docker-compose exec postgres psql -U postgres

# Check connections
\conninfo
\l
```

### Permission Issues
```bash
# Fix permissions
sudo chown -R $USER:$USER .
```

### Reset Everything
```bash
docker-compose down -v
docker system prune -a
docker-compose up -d --build
```

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Generate strong secret keys
- [ ] Set DEBUG=False in production
- [ ] Configure proper ALLOWED_HOSTS
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall (ufw/iptables)
- [ ] Enable database backups
- [ ] Set up monitoring and alerts
- [ ] Regular security updates
- [ ] Implement rate limiting
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Set up log rotation
- [ ] Enable database connection pooling

---

## Updates and Maintenance

### Update Code
```bash
git pull
docker-compose build
docker-compose up -d
docker-compose exec django python manage.py migrate
docker-compose exec django python manage.py collectstatic --noinput
```

### Update Docker Images
```bash
docker-compose pull
docker-compose up -d
```

---

## Performance Tuning

### PostgreSQL
Edit `docker-compose.yml` PostgreSQL environment:
```yaml
POSTGRES_INITDB_ARGS: "-c shared_buffers=256MB -c max_connections=200"
```

### Django Workers
Adjust in `docker-compose.yml`:
```yaml
command: gunicorn config.wsgi:application --bind 0.0.0.0:8001 --workers 8 --timeout 120
```

### FastAPI Workers
```yaml
command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 8
```

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review this guide
3. Check GitHub issues
4. Contact development team

---

## License

[Your License Here]
