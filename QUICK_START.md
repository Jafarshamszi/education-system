# 🚀 Quick Start Guide - Frontend Fixes

## ✅ What Was Fixed

All three frontends had missing module errors. These have been **completely resolved**:

1. ✅ **Admin Frontend** - Missing `@/lib/utils`
2. ✅ **Teacher Frontend** - Missing `@/lib/utils` and `@/lib/api-config`
3. ✅ **Student Frontend** - Missing `@/lib/utils` and `@/lib/api-config`

## 📦 What Was Added

### Admin Frontend (`frontend/`)
```
frontend/src/lib/
└── utils.ts          ← NEW: cn() utility for className merging
```

### Teacher Frontend (`frontend-teacher/`)
```
frontend-teacher/lib/
├── utils.ts          ← NEW: cn() utility for className merging
├── api-config.ts     ← NEW: Centralized API endpoints
└── .env.local        ← NEW: Environment configuration
```

### Student Frontend (`frontend-student/`)
```
frontend-student/lib/
├── utils.ts          ← NEW: cn() utility for className merging
├── api-config.ts     ← NEW: Centralized API endpoints
└── .env.local        ← NEW: Environment configuration
```

## 🎯 Quick Start

### Step 1: Verify Fixes
```powershell
# Run verification script
.\verify-fixes.ps1
```

Expected output: `✅ ALL CHECKS PASSED!` or `⚠️ PASSED WITH WARNINGS`

### Step 2: Start Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The backend should be running at `http://localhost:8000`

### Step 3: Start All Frontends

**Option A: PowerShell Script (Recommended for Windows)**
```powershell
.\start-frontends.ps1
```

**Option B: Bash Script (Linux/Mac)**
```bash
./start-frontends.sh
```

**Option C: Manual (3 separate terminals)**
```bash
# Terminal 1
cd frontend && bun dev

# Terminal 2  
cd frontend-teacher && bun dev

# Terminal 3
cd frontend-student && bun dev
```

## 🌐 Access Your Frontends

| Portal  | URL                       | Port | Purpose        |
|---------|---------------------------|------|----------------|
| Admin   | http://localhost:3000     | 3000 | Administration |
| Teacher | http://localhost:3001     | 3001 | Teacher Portal |
| Student | http://localhost:3002     | 3002 | Student Portal |

## 🔧 Configuration

### API Endpoints
All API calls now go through centralized configuration:

**Backend Base URL:** `http://localhost:8000/api/v1`

### Environment Variables

Teacher & Student frontends use `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=Teacher Portal  # or Student Portal
NEXT_PUBLIC_APP_PORT=3001            # or 3002
```

To change the backend URL, edit these `.env.local` files.

## 📝 Key Features

### 1. Utils (`lib/utils.ts`)
```typescript
import { cn } from "@/lib/utils"

// Merge Tailwind classes intelligently
<div className={cn("base-class", isActive && "active-class", className)} />
```

### 2. API Config (`lib/api-config.ts`)
```typescript
import { API_ENDPOINTS } from '@/lib/api-config'

// Login
await axios.post(API_ENDPOINTS.AUTH.LOGIN, { username, password })

// Get data
await axios.get(API_ENDPOINTS.TEACHERS.BY_ID(teacherId))
```

## 🐛 Troubleshooting

### Build Errors Still Showing?

1. **Clear build cache:**
   ```bash
   cd frontend && rm -rf .next
   cd ../frontend-teacher && rm -rf .next
   cd ../frontend-student && rm -rf .next
   ```

2. **Reinstall dependencies:**
   ```bash
   cd frontend && bun install
   cd ../frontend-teacher && bun install
   cd ../frontend-student && bun install
   ```

3. **Restart dev servers**

### Port Already in Use?

```powershell
# Find process using port
Get-NetTCPConnection -LocalPort 3000 | Select-Object OwningProcess

# Kill it
Stop-Process -Id <PID> -Force
```

Or kill all bun processes:
```powershell
Get-Process | Where-Object {$_.ProcessName -eq 'bun'} | Stop-Process -Force
```

### Backend Not Responding?

1. Check backend is running: `http://localhost:8000/health`
2. Check CORS settings in `backend/app/main.py`
3. Verify database connection in `backend/.env`

## 📚 Documentation

For detailed information, see:
- `FRONTEND_SETUP_FIXES.md` - Complete technical documentation
- `start-frontends.ps1` - PowerShell startup script
- `start-frontends.sh` - Bash startup script
- `verify-fixes.ps1` - Verification script

## 🎉 Success Indicators

You'll know everything is working when:

1. ✅ Verification script passes all checks
2. ✅ Backend responds at `http://localhost:8000/health`
3. ✅ All three frontends start without errors
4. ✅ You can access all three URLs listed above
5. ✅ No "Module not found" errors in browser console

## 💡 Tips

- Use PowerShell scripts for easier management
- Check `.next` folders if issues persist (delete them)
- Backend must be running before testing API calls
- Use browser DevTools to check network requests
- Environment variables require server restart to take effect

## 🔗 API Structure

```
http://localhost:8000/api/v1/
├── /auth              ← Authentication & user management
├── /teachers          ← Teacher data & operations
├── /students          ← Student data & operations
├── /curriculum        ← Courses & subjects
├── /class-schedule    ← Scheduling
├── /evaluation-system ← Grades & attendance
└── /dashboard         ← Dashboard data
```

## ✨ What's Next?

Now that all build errors are fixed, you can:

1. **Develop Features** - All imports work correctly
2. **Test API Integration** - Centralized endpoints ready
3. **Customize Styling** - `cn()` utility available everywhere
4. **Deploy** - Production-ready configuration

---

**Status:** ✅ All Build Errors Resolved  
**Last Updated:** 2024  
**Ready for Development:** YES 🎉