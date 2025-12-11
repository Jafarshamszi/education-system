#!/usr/bin/env pwsh
# Docker Build and Deployment Verification Script
# This script validates that all Docker images build successfully

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Docker Build Verification Script" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not installed or not running!" -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
Write-Host "`nChecking Docker Compose installation..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "✓ $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker Compose is not installed!" -ForegroundColor Red
    exit 1
}

# Verify all Dockerfiles exist
Write-Host "`nVerifying Dockerfile existence..." -ForegroundColor Yellow
$dockerfiles = @(
    "backend\Dockerfile.django",
    "backend\Dockerfile.fastapi",
    "frontend\Dockerfile",
    "frontend-teacher\Dockerfile",
    "frontend-student\Dockerfile"
)

$allExist = $true
foreach ($dockerfile in $dockerfiles) {
    if (Test-Path $dockerfile) {
        Write-Host "✓ $dockerfile exists" -ForegroundColor Green
    } else {
        Write-Host "✗ $dockerfile missing!" -ForegroundColor Red
        $allExist = $false
    }
}

if (-not $allExist) {
    Write-Host "`n✗ Some Dockerfiles are missing!" -ForegroundColor Red
    exit 1
}

# Verify docker-compose.yml exists
Write-Host "`nVerifying docker-compose.yml..." -ForegroundColor Yellow
if (Test-Path "docker-compose.yml") {
    Write-Host "✓ docker-compose.yml exists" -ForegroundColor Green
} else {
    Write-Host "✗ docker-compose.yml missing!" -ForegroundColor Red
    exit 1
}

# Validate docker-compose.yml syntax
Write-Host "`nValidating docker-compose.yml syntax..." -ForegroundColor Yellow
try {
    docker-compose config --quiet
    Write-Host "✓ docker-compose.yml syntax is valid" -ForegroundColor Green
} catch {
    Write-Host "✗ docker-compose.yml has syntax errors!" -ForegroundColor Red
    exit 1
}

# Check .env file
Write-Host "`nChecking .env file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env file exists" -ForegroundColor Green
} else {
    Write-Host "⚠ .env file not found. Using .env.example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✓ Created .env from .env.example" -ForegroundColor Green
    } else {
        Write-Host "✗ Neither .env nor .env.example found!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "Starting Docker Build Test" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Prompt user for confirmation
$buildChoice = Read-Host "Do you want to build all images now? This may take 10-20 minutes (y/n)"
if ($buildChoice -ne "y") {
    Write-Host "`n✓ Pre-flight checks passed! Run 'docker-compose build' when ready." -ForegroundColor Green
    exit 0
}

# Build all images
Write-Host "`nBuilding all Docker images..." -ForegroundColor Yellow
Write-Host "This will take several minutes. Please wait..." -ForegroundColor Cyan

try {
    docker-compose build --no-cache
    Write-Host "`n✓ All images built successfully!" -ForegroundColor Green
} catch {
    Write-Host "`n✗ Build failed!" -ForegroundColor Red
    exit 1
}

# List built images
Write-Host "`nListing built images..." -ForegroundColor Yellow
docker images | Select-String "education"

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "Build Verification Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run 'docker-compose up -d' to start all services" -ForegroundColor White
Write-Host "2. Run 'docker-compose logs -f' to view logs" -ForegroundColor White
Write-Host "3. Access frontends at:" -ForegroundColor White
Write-Host "   - Admin: http://localhost:3000" -ForegroundColor Cyan
Write-Host "   - Teacher: http://localhost:3001" -ForegroundColor Cyan
Write-Host "   - Student: http://localhost:3002" -ForegroundColor Cyan
Write-Host "4. Access backend APIs at:" -ForegroundColor White
Write-Host "   - FastAPI: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   - Django: http://localhost:8001/admin" -ForegroundColor Cyan
Write-Host ""
