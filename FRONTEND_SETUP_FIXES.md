# Frontend Setup Fixes Documentation

## 🎯 Overview

This document outlines the fixes applied to resolve build errors across all three frontend applications (Admin, Teacher, and Student portals).

## 🐛 Issues Identified

### 1. Admin Frontend (`frontend/`)
**Error:** `Module not found: Can't resolve '@/lib/utils'`

**Root Cause:** Missing utility file that provides the `cn()` function used throughout UI components for className merging.

### 2. Teacher Frontend (`frontend-teacher/`)
**Errors:**
- `Module not found: Can't resolve '@/lib/api-config'`
- `Module not found: Can't resolve '@/lib/utils'`

**Root Cause:** Missing API configuration file and utility functions.

### 3. Student Frontend (`frontend-student/`)
**Errors:**
- `Module not found: Can't resolve '@/lib/api-config'`
- `Module not found: Can't resolve '@/lib/utils'`

**Root Cause:** Missing API configuration file and utility functions.

---

## ✅ Solutions Implemented

### 1. Created `lib/utils.ts` for all frontends

**Location:** 
- `frontend/src/lib/utils.ts` (Admin)
- `frontend-teacher/lib/utils.ts` (Teacher)
- `frontend-student/lib/utils.ts` (Student)

**Purpose:** Provides the `cn()` utility function for merging Tailwind CSS classes intelligently.

**Content:**
```typescript
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

**Dependencies Used:**
- `clsx` - For conditional class name composition
- `tailwind-merge` - For intelligently merging Tailwind classes

---

### 2. Created `lib/api-config.ts` for Teacher Frontend

**Location:** `frontend-teacher/lib/api-config.ts`

**Purpose:** Centralized API endpoint configuration for the Teacher Portal.

**Features:**
- ✅ Authentication endpoints (login, logout, refresh, profile)
- ✅ Teacher-specific endpoints (schedule, courses, students)
- ✅ Course and subject management
- ✅ Student information access
- ✅ Schedule management
- ✅ Evaluation system (grades, attendance)
- ✅ Dashboard endpoints

**Environment Variable:** 
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

**Key Endpoints:**
```typescript
AUTH: {
  LOGIN: '/auth/login',
  USER: '/auth/user',
  PROFILE: '/auth/profile'
}
TEACHERS: {
  BY_ID: (id) => `/teachers/${id}`,
  SCHEDULE: (id) => `/teachers/${id}/schedule`,
  COURSES: (id) => `/teachers/${id}/courses`
}
```

---

### 3. Created `lib/api-config.ts` for Student Frontend

**Location:** `frontend-student/lib/api-config.ts`

**Purpose:** Centralized API endpoint configuration for the Student Portal.

**Features:**
- ✅ Authentication endpoints
- ✅ Student profile and data
- ✅ Course enrollment and information
- ✅ Schedule viewing (weekly, daily)
- ✅ Grades and transcripts
- ✅ Attendance tracking
- ✅ Student groups
- ✅ Dashboard endpoints
- ✅ Teacher information lookup

**Environment Variable:** 
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

**Key Endpoints:**
```typescript
AUTH: {
  LOGIN: '/auth/login',
  USER: '/auth/user',
  PROFILE: '/auth/profile'
}
STUDENTS: {
  BY_ID: (id) => `/students/${id}`,
  GRADES: (id) => `/students/${id}/grades`,
  SCHEDULE: (id) => `/students/${id}/schedule`
}
```

---

### 4. Created Environment Configuration Files

**Teacher Frontend:** `frontend-teacher/.env.local`
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=Teacher Portal
NEXT_PUBLIC_APP_PORT=3001
```

**Student Frontend:** `frontend-student/.env.local`
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=Student Portal
NEXT_PUBLIC_APP_PORT=3002
```

---

## 📁 File Structure

```
Education-system/
├── frontend/                      # Admin Portal (Port 3000)
│   └── src/
│       └── lib/
│           └── utils.ts          ✅ NEW
│
├── frontend-teacher/              # Teacher Portal (Port 3001)
│   ├── lib/
│   │   ├── api-config.ts         ✅ NEW
│   │   └── utils.ts              ✅ NEW
│   └── .env.local                ✅ NEW
│
└── frontend-student/              # Student Portal (Port 3002)
    ├── lib/
    │   ├── api-config.ts         ✅ NEW
    │   └── utils.ts              ✅ NEW
    └── .env.local                ✅ NEW
```

---

## 🔧 Path Aliases Configuration

### Admin Frontend (`frontend/tsconfig.json`)
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Teacher & Student Frontends
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

---

## 🚀 How to Run All Frontends

### Option 1: PowerShell Script (Windows)
```powershell
.\start-frontends.ps1
```

### Option 2: Bash Script (Linux/Mac)
```bash
./start-frontends.sh
```

### Option 3: Manual Start
```bash
# Terminal 1 - Admin
cd frontend && bun dev

# Terminal 2 - Teacher
cd frontend-teacher && bun dev

# Terminal 3 - Student
cd frontend-student && bun dev
```

---

## 🌐 Access URLs

| Portal   | URL                          | Port |
|----------|------------------------------|------|
| Admin    | http://localhost:3000        | 3000 |
| Teacher  | http://localhost:3001        | 3001 |
| Student  | http://localhost:3002        | 3002 |

---

## 📦 Dependencies

All required dependencies are already installed in `package.json`:

- ✅ `clsx` - ^2.1.1
- ✅ `tailwind-merge` - ^3.3.1
- ✅ `class-variance-authority` - ^0.7.1
- ✅ `axios` - ^1.12.2

---

## 🔍 Verification

Run diagnostics to ensure no errors:
```bash
# Check each frontend
bun run build  # in each frontend directory
```

All files pass diagnostics without errors or warnings! ✅

---

## 🎨 Usage Examples

### Using the `cn()` utility:
```typescript
import { cn } from "@/lib/utils"

<div className={cn(
  "base-classes",
  isActive && "active-classes",
  className
)} />
```

### Using API endpoints:
```typescript
import { API_ENDPOINTS } from '@/lib/api-config'
import axios from 'axios'

// Login
const response = await axios.post(API_ENDPOINTS.AUTH.LOGIN, {
  username: 'user',
  password: 'pass'
})

// Get teacher schedule
const schedule = await axios.get(
  API_ENDPOINTS.TEACHERS.SCHEDULE(teacherId),
  { headers: { Authorization: `Bearer ${token}` } }
)
```

---

## 🔐 Backend Integration

The API endpoints are configured to connect to:
- **Base URL:** `http://localhost:8000/api/v1`
- **Backend Framework:** FastAPI
- **Authentication:** JWT Bearer tokens

### Backend API Structure:
```
/api/v1
├── /auth          # Authentication
├── /teachers      # Teacher management
├── /students      # Student management
├── /curriculum    # Courses & subjects
├── /class-schedule # Scheduling
├── /evaluation-system # Grades & attendance
└── /dashboard     # Dashboard data
```

---

## 📝 Notes

1. **Environment Variables:** The `.env.local` files are git-ignored for security
2. **API URL:** Can be changed by updating `NEXT_PUBLIC_API_URL` in `.env.local`
3. **Hot Reload:** All frontends support hot module replacement (HMR)
4. **TypeScript:** All configurations use strict TypeScript checking

---

## 🎯 Next Steps

1. ✅ Build errors resolved
2. ✅ API configuration centralized
3. ✅ Utility functions available
4. ✅ Environment variables configured
5. 🔄 Ready for development!

---

## 📞 Support

If you encounter any issues:
1. Ensure all dependencies are installed: `bun install`
2. Check that the backend is running on port 8000
3. Verify environment variables in `.env.local` files
4. Clear `.next` cache: `rm -rf .next`

---

**Last Updated:** 2024
**Status:** ✅ All Build Errors Resolved