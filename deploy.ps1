# Education System - Quick Deployment Script (Windows)
# Run this with PowerShell

Write-Host "🚀 Education System Deployment Script" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

# Check if Docker is installed
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker and Docker Compose are installed" -ForegroundColor Green
Write-Host ""

# Check if .env exists
if (!(Test-Path .env)) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
        Write-Host "⚠️  Please edit .env file and update the passwords and secret keys!" -ForegroundColor Yellow
        Write-Host "   Then run this script again."
        exit 0
    } else {
        Write-Host "❌ .env.example not found!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ .env file found" -ForegroundColor Green
Write-Host ""

# Ask for deployment type
Write-Host "Select deployment type:"
Write-Host "1) Development (local)"
Write-Host "2) Production (with SSL)"
$deployment_type = Read-Host "Enter choice [1-2]"

if ($deployment_type -eq "2") {
    Write-Host ""
    Write-Host "🔒 Production Deployment Selected" -ForegroundColor Cyan
    Write-Host ""
    
    # Check for SSL certificates
    if (!(Test-Path ./nginx/ssl/fullchain.pem) -or !(Test-Path ./nginx/ssl/privkey.pem)) {
        Write-Host "⚠️  SSL certificates not found!" -ForegroundColor Yellow
        Write-Host "   For production, you need to set up SSL certificates first."
        Write-Host ""
        exit 1
    }
    
    # Use SSL nginx config
    if (Test-Path ./nginx/conf.d/education-system-ssl.conf) {
        Copy-Item ./nginx/conf.d/education-system-ssl.conf ./nginx/conf.d/education-system.conf -Force
        Write-Host "✅ SSL configuration enabled" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "🔨 Building Docker images..." -ForegroundColor Cyan
docker-compose build

Write-Host ""
Write-Host "🚀 Starting services..." -ForegroundColor Cyan
docker-compose up -d

Write-Host ""
Write-Host "⏳ Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "📊 Running database migrations..." -ForegroundColor Cyan
docker-compose exec -T django python manage.py migrate

Write-Host ""
Write-Host "📦 Collecting static files..." -ForegroundColor Cyan
docker-compose exec -T django python manage.py collectstatic --noinput

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Service URLs:" -ForegroundColor Cyan
if ($deployment_type -eq "1") {
    Write-Host "   Admin Frontend:   http://localhost:3000" -ForegroundColor White
    Write-Host "   Teacher Frontend: http://localhost:3001" -ForegroundColor White
    Write-Host "   Student Frontend: http://localhost:3002" -ForegroundColor White
    Write-Host "   Django Admin:     http://localhost:8001/admin/" -ForegroundColor White
    Write-Host "   FastAPI Docs:     http://localhost:8000/docs" -ForegroundColor White
} else {
    Write-Host "   Admin Frontend:   https://admin.yourdomain.com" -ForegroundColor White
    Write-Host "   Teacher Frontend: https://teacher.yourdomain.com" -ForegroundColor White
    Write-Host "   Student Frontend: https://student.yourdomain.com" -ForegroundColor White
    Write-Host "   API:              https://api.yourdomain.com" -ForegroundColor White
}

Write-Host ""
Write-Host "🔍 To view logs: docker-compose logs -f" -ForegroundColor Yellow
Write-Host "🛑 To stop: docker-compose stop" -ForegroundColor Yellow
Write-Host "🔄 To restart: docker-compose restart" -ForegroundColor Yellow
Write-Host ""

# Ask if user wants to create superuser
$create_superuser = Read-Host "Do you want to create a Django superuser now? (y/n)"
if ($create_superuser -eq "y" -or $create_superuser -eq "Y") {
    Write-Host ""
    docker-compose exec django python manage.py createsuperuser
}

Write-Host ""
Write-Host "✨ All done! Your Education System is now running!" -ForegroundColor Green
Write-Host ""
