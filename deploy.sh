#!/bin/bash

# Education System - Quick Deployment Script
# This script automates the deployment process

set -e

echo "🚀 Education System Deployment Script"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "⚠️  Please edit .env file and update the passwords and secret keys!"
        echo "   Then run this script again."
        exit 0
    else
        echo "❌ .env.example not found!"
        exit 1
    fi
fi

echo "✅ .env file found"
echo ""

# Ask for deployment type
echo "Select deployment type:"
echo "1) Development (local)"
echo "2) Production (with SSL)"
read -p "Enter choice [1-2]: " deployment_type

if [ "$deployment_type" == "2" ]; then
    echo ""
    echo "🔒 Production Deployment Selected"
    echo ""
    
    # Check for SSL certificates
    if [ ! -f ./nginx/ssl/fullchain.pem ] || [ ! -f ./nginx/ssl/privkey.pem ]; then
        echo "⚠️  SSL certificates not found!"
        echo "   Please run the following commands first:"
        echo ""
        echo "   sudo apt-get install certbot"
        echo "   docker-compose stop nginx"
        echo "   sudo certbot certonly --standalone -d admin.yourdomain.com -d teacher.yourdomain.com -d student.yourdomain.com -d api.yourdomain.com"
        echo "   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/"
        echo "   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/"
        echo ""
        exit 1
    fi
    
    # Use SSL nginx config
    if [ -f ./nginx/conf.d/education-system-ssl.conf ]; then
        cp ./nginx/conf.d/education-system-ssl.conf ./nginx/conf.d/education-system.conf
        echo "✅ SSL configuration enabled"
    fi
fi

echo ""
echo "🔨 Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for database to be ready..."
sleep 10

echo ""
echo "📊 Running database migrations..."
docker-compose exec -T django python manage.py migrate

echo ""
echo "📦 Collecting static files..."
docker-compose exec -T django python manage.py collectstatic --noinput

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Service URLs:"
if [ "$deployment_type" == "1" ]; then
    echo "   Admin Frontend:   http://localhost:3000"
    echo "   Teacher Frontend: http://localhost:3001"
    echo "   Student Frontend: http://localhost:3002"
    echo "   Django Admin:     http://localhost:8001/admin/"
    echo "   FastAPI Docs:     http://localhost:8000/docs"
else
    echo "   Admin Frontend:   https://admin.yourdomain.com"
    echo "   Teacher Frontend: https://teacher.yourdomain.com"
    echo "   Student Frontend: https://student.yourdomain.com"
    echo "   API:              https://api.yourdomain.com"
fi

echo ""
echo "🔍 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose stop"
echo "🔄 To restart: docker-compose restart"
echo ""

# Ask if user wants to create superuser
read -p "Do you want to create a Django superuser now? (y/n): " create_superuser
if [ "$create_superuser" == "y" ] || [ "$create_superuser" == "Y" ]; then
    echo ""
    docker-compose exec django python manage.py createsuperuser
fi

echo ""
echo "✨ All done! Your Education System is now running!"
echo ""
