#!/usr/bin/env pwsh

# Verification script for frontend fixes
# Checks that all required files and configurations are in place

Write-Host "🔍 Verifying Frontend Fixes..." -ForegroundColor Cyan
Write-Host ""

$PROJECT_DIR = $PSScriptRoot
$errors = @()
$warnings = @()
$success = @()

# Function to check file exists
function Test-FileExists {
    param(
        [string]$Path,
        [string]$Description
    )

    if (Test-Path $Path) {
        Write-Host "✅ $Description" -ForegroundColor Green
        $script:success += $Description
        return $true
    } else {
        Write-Host "❌ $Description" -ForegroundColor Red
        $script:errors += $Description
        return $false
    }
}

# Function to check file contains text
function Test-FileContains {
    param(
        [string]$Path,
        [string]$Pattern,
        [string]$Description
    )

    if (Test-Path $Path) {
        $content = Get-Content $Path -Raw
        if ($content -match $Pattern) {
            Write-Host "✅ $Description" -ForegroundColor Green
            $script:success += $Description
            return $true
        } else {
            Write-Host "⚠️  $Description - File exists but pattern not found" -ForegroundColor Yellow
            $script:warnings += $Description
            return $false
        }
    } else {
        Write-Host "❌ $Description - File not found" -ForegroundColor Red
        $script:errors += $Description
        return $false
    }
}

Write-Host "📁 Checking Admin Frontend (frontend/)..." -ForegroundColor Yellow
Write-Host ""

Test-FileExists "$PROJECT_DIR\frontend\src\lib\utils.ts" "Admin: utils.ts exists"
Test-FileContains "$PROJECT_DIR\frontend\src\lib\utils.ts" "export function cn" "Admin: cn function defined"
Test-FileContains "$PROJECT_DIR\frontend\tsconfig.json" '"@/\*": \["./src/\*"\]' "Admin: Path alias configured"

Write-Host ""
Write-Host "📁 Checking Teacher Frontend (frontend-teacher/)..." -ForegroundColor Yellow
Write-Host ""

Test-FileExists "$PROJECT_DIR\frontend-teacher\lib\utils.ts" "Teacher: utils.ts exists"
Test-FileExists "$PROJECT_DIR\frontend-teacher\lib\api-config.ts" "Teacher: api-config.ts exists"
Test-FileContains "$PROJECT_DIR\frontend-teacher\lib\utils.ts" "export function cn" "Teacher: cn function defined"
Test-FileContains "$PROJECT_DIR\frontend-teacher\lib\api-config.ts" "API_ENDPOINTS" "Teacher: API_ENDPOINTS defined"
Test-FileContains "$PROJECT_DIR\frontend-teacher\lib\api-config.ts" "AUTH" "Teacher: AUTH endpoints defined"
Test-FileExists "$PROJECT_DIR\frontend-teacher\.env.local" "Teacher: .env.local exists"
Test-FileContains "$PROJECT_DIR\frontend-teacher\.env.local" "NEXT_PUBLIC_API_URL" "Teacher: API URL configured"
Test-FileContains "$PROJECT_DIR\frontend-teacher\tsconfig.json" '"@/\*": \["./*"\]' "Teacher: Path alias configured"

Write-Host ""
Write-Host "📁 Checking Student Frontend (frontend-student/)..." -ForegroundColor Yellow
Write-Host ""

Test-FileExists "$PROJECT_DIR\frontend-student\lib\utils.ts" "Student: utils.ts exists"
Test-FileExists "$PROJECT_DIR\frontend-student\lib\api-config.ts" "Student: api-config.ts exists"
Test-FileContains "$PROJECT_DIR\frontend-student\lib\utils.ts" "export function cn" "Student: cn function defined"
Test-FileContains "$PROJECT_DIR\frontend-student\lib\api-config.ts" "API_ENDPOINTS" "Student: API_ENDPOINTS defined"
Test-FileContains "$PROJECT_DIR\frontend-student\lib\api-config.ts" "AUTH" "Student: AUTH endpoints defined"
Test-FileExists "$PROJECT_DIR\frontend-student\.env.local" "Student: .env.local exists"
Test-FileContains "$PROJECT_DIR\frontend-student\.env.local" "NEXT_PUBLIC_API_URL" "Student: API URL configured"
Test-FileContains "$PROJECT_DIR\frontend-student\tsconfig.json" '"@/\*": \["./*"\]' "Student: Path alias configured"

Write-Host ""
Write-Host "📦 Checking Dependencies..." -ForegroundColor Yellow
Write-Host ""

Test-FileContains "$PROJECT_DIR\frontend\package.json" "clsx" "Admin: clsx dependency"
Test-FileContains "$PROJECT_DIR\frontend\package.json" "tailwind-merge" "Admin: tailwind-merge dependency"
Test-FileContains "$PROJECT_DIR\frontend-teacher\package.json" "clsx" "Teacher: clsx dependency"
Test-FileContains "$PROJECT_DIR\frontend-teacher\package.json" "tailwind-merge" "Teacher: tailwind-merge dependency"
Test-FileContains "$PROJECT_DIR\frontend-student\package.json" "clsx" "Student: clsx dependency"
Test-FileContains "$PROJECT_DIR\frontend-student\package.json" "tailwind-merge" "Student: tailwind-merge dependency"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                    SUMMARY" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "✅ Passed: $($success.Count)" -ForegroundColor Green
if ($warnings.Count -gt 0) {
    Write-Host "⚠️  Warnings: $($warnings.Count)" -ForegroundColor Yellow
}
if ($errors.Count -gt 0) {
    Write-Host "❌ Errors: $($errors.Count)" -ForegroundColor Red
}

Write-Host ""

if ($errors.Count -gt 0) {
    Write-Host "❌ VERIFICATION FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Missing or invalid files:" -ForegroundColor Red
    foreach ($error in $errors) {
        Write-Host "  - $error" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Please run the setup again or check the FRONTEND_SETUP_FIXES.md documentation" -ForegroundColor Yellow
    exit 1
} elseif ($warnings.Count -gt 0) {
    Write-Host "⚠️  VERIFICATION PASSED WITH WARNINGS" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Warnings:" -ForegroundColor Yellow
    foreach ($warning in $warnings) {
        Write-Host "  - $warning" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "You may proceed but review the warnings above." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "✅ ALL CHECKS PASSED!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎉 All frontend fixes are in place and verified!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Start the backend: cd backend && uvicorn app.main:app --reload" -ForegroundColor White
    Write-Host "  2. Start frontends: .\start-frontends.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "Access URLs:" -ForegroundColor Cyan
    Write-Host "  Admin:   http://localhost:3000" -ForegroundColor White
    Write-Host "  Teacher: http://localhost:3001" -ForegroundColor White
    Write-Host "  Student: http://localhost:3002" -ForegroundColor White
    Write-Host ""
    exit 0
}
