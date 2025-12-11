#!/usr/bin/env pwsh

# Start all three frontends in separate terminal sessions
# Usage: .\start-frontends.ps1

$PROJECT_DIR = $PSScriptRoot

Write-Host "🚀 Starting all frontends..." -ForegroundColor Cyan

# Check if bun is installed
if (-not (Get-Command bun -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Error: Bun is not installed" -ForegroundColor Red
    Write-Host "Install it from: https://bun.sh" -ForegroundColor Yellow
    exit 1
}

# Function to start a frontend
function Start-Frontend {
    param(
        [string]$Name,
        [int]$Port,
        [string]$Dir
    )

    Write-Host "Starting $Name on port $Port..." -ForegroundColor Yellow

    # Check if directory exists
    if (-not (Test-Path $Dir)) {
        Write-Host "❌ Error: Directory $Dir does not exist" -ForegroundColor Red
        return $false
    }

    # Check if port is already in use
    $portInUse = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($portInUse) {
        Write-Host "⚠️  Warning: Port $Port is already in use" -ForegroundColor Yellow
        Write-Host "   Kill the process with: Stop-Process -Id $($portInUse.OwningProcess) -Force" -ForegroundColor Gray
        return $false
    }

    # Start in new window
    $process = Start-Process -FilePath "bun" -ArgumentList "dev" -WorkingDirectory $Dir -PassThru -WindowStyle Normal

    if ($process) {
        Write-Host "✅ $Name started (PID: $($process.Id))" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ Failed to start $Name" -ForegroundColor Red
        return $false
    }
}

# Start each frontend
Start-Frontend -Name "Admin Frontend" -Port 3000 -Dir "$PROJECT_DIR\frontend"
Start-Sleep -Seconds 2

Start-Frontend -Name "Teacher Frontend" -Port 3001 -Dir "$PROJECT_DIR\frontend-teacher"
Start-Sleep -Seconds 2

Start-Frontend -Name "Student Frontend" -Port 3002 -Dir "$PROJECT_DIR\frontend-student"
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "✨ All frontends started!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Access URLs:" -ForegroundColor Cyan
Write-Host "   Admin:   http://localhost:3000" -ForegroundColor White
Write-Host "   Teacher: http://localhost:3001" -ForegroundColor White
Write-Host "   Student: http://localhost:3002" -ForegroundColor White
Write-Host ""
Write-Host "To stop all frontends:" -ForegroundColor Yellow
Write-Host "   Get-Process | Where-Object {`$_.ProcessName -eq 'bun'} | Stop-Process -Force" -ForegroundColor Gray
Write-Host ""
Write-Host "To view running processes:" -ForegroundColor Yellow
Write-Host "   Get-Process bun" -ForegroundColor Gray
Write-Host ""
