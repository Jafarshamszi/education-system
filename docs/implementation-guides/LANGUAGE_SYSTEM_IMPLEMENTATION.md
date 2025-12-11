# Complete Language System Implementation

## Overview
Implemented a comprehensive multilingual system with backend persistence that allows users to:
- Save language preferences per user in the database
- Automatically load their preferred language on login
- See localized content from JSONB database fields
- Have language changes persist across sessions

## What Was Implemented

### 1. Backend - User Preferences API ✅

**File**: `/backend/app/api/user_preferences.py`

**Endpoints Created**:
- `GET /api/v1/user-preferences/` - Get all user preferences including language
- `PUT /api/v1/user-preferences/language` - Update only language preference
- `PUT /api/v1/user-preferences/` - Update all preferences

**Features**:
- Validates language (must be 'en', 'ru', or 'az')
- Automatically creates default preferences if none exist
- Saves to `user_preferences` table with `language` column

**Database Table Used**: `user_preferences`
```sql
language TEXT DEFAULT 'az'
```

### 2. Backend - Language-Aware Endpoints ✅

#### Dashboard Endpoint Updated
**File**: `/backend/app/api/dashboard.py`

**Changes**:
- Added `lang` parameter to `/dashboard/stats` endpoint
- Uses language to fetch localized course names from JSONB fields
- Query example:
```sql
COALESCE(c.name->>%s, c.name->>'en', c.name->>'az') as course_name
```

#### Teachers Endpoint Updated
**File**: `/backend/app/api/teachers.py`

**Changes**:
- Added `lang` parameter to all teacher endpoints
- Added `name_localized` field to `OrganizationInfo` model
- Created `get_localized_name()` helper function
- Returns localized organization names based on user's language

**Helper Function**:
```python
def get_localized_name(name_dict: Optional[dict], lang: str = 'en') -> Optional[str]:
    """Get localized name from JSONB field with fallback"""
    if not name_dict:
        return None
    return name_dict.get(lang) or name_dict.get('en') or name_dict.get('az') or next(iter(name_dict.values()), None)
```

#### Organization Endpoint Updated
**File**: `/backend/app/api/organization.py`

**Changes**:
- Added `lang` parameter to `/organizations/hierarchy` endpoint
- Added `name_localized` field to response
- Uses `get_localized_value()` helper for JSONB field extraction

### 3. Frontend - Language Context Enhanced ✅

**File**: `/frontend/src/contexts/LanguageContext.tsx`

**Major Updates**:
1. **Fetches from Backend**: On mount, fetches user's saved language preference
2. **Saves to Backend**: When language changes, saves to database AND localStorage
3. **Added `isLoading` state**: Handles async language loading gracefully
4. **Fallback Logic**: If backend fails or user not logged in, uses localStorage

**Key Code**:
```typescript
useEffect(() => {
  const fetchUserLanguage = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        const response = await axios.get('http://localhost:8000/api/v1/user-preferences/', {
          headers: { Authorization: `Bearer ${token}` }
        });
        const userLang = response.data.language;
        if (userLang && ['en', 'ru', 'az'].includes(userLang)) {
          setLanguageState(userLang);
          localStorage.setItem('language', userLang);
        }
      }
    } catch (error) {
      // Fallback to localStorage
    }
  };
  fetchUserLanguage();
}, []);

const setLanguage = async (lang: Language) => {
  setLanguageState(lang);
  localStorage.setItem('language', lang);

  // Save to backend
  try {
    const token = localStorage.getItem('access_token');
    if (token) {
      await axios.put(
        'http://localhost:8000/api/v1/user-preferences/language',
        { language: lang },
        { headers: { Authorization: `Bearer ${token}` } }
      );
    }
  } catch (error) {
    console.error('Failed to save language preference');
  }
};
```

**Translation Keys Added**:
- `common.*` - enabled, disabled, blocked, etc.
- `dashboard.*` - All dashboard labels with proper fallbacks
- `sidebar.*` - All navigation items
- `settings.*` - Settings page labels

### 4. Frontend - Dashboard Updated ✅

**File**: `/frontend/src/app/dashboard/page.tsx`

**Changes**:
1. **Sends language parameter** to backend API calls:
```typescript
axios.get("http://localhost:8000/api/v1/dashboard/stats", {
  headers,
  params: { lang: language }
})
```

2. **Refetches on language change**:
```typescript
useEffect(() => {
  fetchDashboardData();
}, [language]); // Refetch when language changes
```

3. **All UI text translated** using `t()` function

### 5. Frontend - Sidebar Updated ✅

**File**: `/frontend/src/components/app-sidebar.tsx`

**Changes**:
- Converted from static `data` object to dynamic function component
- Uses `useLanguage()` hook to access `t()` function
- All menu items and section headers translated
- Updates automatically when language changes

**Before**:
```typescript
const data = {
  navMain: [{ title: "Dashboard", url: "/dashboard", icon: IconDashboard }]
}
```

**After**:
```typescript
export function AppSidebar({ ...props }) {
  const { t } = useLanguage();

  const data = {
    navMain: [{ title: t("sidebar.dashboard"), url: "/dashboard", icon: IconDashboard }]
  };

  return (...)
}
```

### 6. Frontend - Settings Page Updated ✅

**File**: `/frontend/src/app/dashboard/settings/page.tsx`

**Changes**:
- Removed local translation logic (90+ lines removed)
- Uses global `useLanguage()` hook
- All `getTranslation()` calls replaced with `t()`
- Language changes now update entire app

## How The System Works Now

### User Flow:

1. **User Logs In**
   - Backend creates default preferences if none exist (language: 'az')
   - JWT token stored in localStorage

2. **App Loads**
   - LanguageContext fetches GET `/api/v1/user-preferences/`
   - Extracts user's saved language
   - Updates UI with saved language
   - All components using `t()` render in user's language

3. **User Changes Language in Settings**
   - Calls `setLanguage('ru')` from context
   - Context updates state (triggers re-render)
   - Context saves to localStorage (for offline access)
   - Context calls PUT `/api/v1/user-preferences/language` (persists to database)

4. **Language Change Propagates**
   - All components using `t()` re-render with new language
   - Dashboard refetches data with `lang` parameter
   - Backend returns localized JSONB field values
   - Navigation, labels, and database content all update

5. **User Logs Out and Back In**
   - Language preference automatically restored from database
   - No need to change language again

### Data Flow Diagram:

```
User Login
    ↓
Frontend: LanguageContext.useEffect()
    ↓
GET /api/v1/user-preferences/ → Returns {language: 'ru', ...}
    ↓
Frontend: setLanguageState('ru')
    ↓
All components re-render with Russian translations
    ↓
User Changes Language to 'en'
    ↓
Frontend: setLanguage('en')
    ↓
    ├─→ localStorage.setItem('language', 'en')
    ├─→ PUT /api/v1/user-preferences/language {language: 'en'}
    └─→ Database: UPDATE user_preferences SET language = 'en'
    ↓
Frontend: Dashboard refetches with ?lang=en
    ↓
Backend: Returns localized course names, org names using JSONB->>'en'
    ↓
UI displays everything in English
```

## Database Schema

### JSONB Field Pattern

Many tables store localized content in JSONB format:

**courses table**:
```json
name: {
  "en": "Introduction to Programming",
  "ru": "Введение в программирование",
  "az": "Proqramlaşdırmaya Giriş"
}
```

**organization_units table**:
```json
name: {
  "en": "Faculty of Engineering",
  "ru": "Инженерный факультет",
  "az": "Mühəndislik Fakültəsi"
}
```

### Backend Query Pattern

When fetching localized data:
```sql
SELECT
  id,
  code,
  COALESCE(
    name->>'${lang}',    -- Try requested language
    name->>'en',         -- Fallback to English
    name->>'az'          -- Fallback to Azerbaijani
  ) as name_localized
FROM organization_units
```

## Files Modified

### Backend Files:
1. `/backend/app/api/user_preferences.py` - **CREATED** ✨
2. `/backend/app/api/__init__.py` - Registered user_preferences router
3. `/backend/app/api/dashboard.py` - Added lang parameter, localized queries
4. `/backend/app/api/teachers.py` - Added lang parameter, localized organization names
5. `/backend/app/api/organization.py` - Added lang parameter, localized names

### Frontend Files:
1. `/frontend/src/contexts/LanguageContext.tsx` - Backend integration, 80+ translation keys
2. `/frontend/src/app/dashboard/page.tsx` - Sends lang parameter, refetches on change
3. `/frontend/src/app/dashboard/settings/page.tsx` - Uses global context
4. `/frontend/src/components/app-sidebar.tsx` - Dynamic translations

## Translation Keys Available

### Common
- `common.loading`, `common.error`, `common.retry`
- `common.save`, `common.cancel`, `common.edit`, `common.delete`
- `common.search`, `common.filter`, `common.export`, `common.import`
- `common.enabled`, `common.disabled`, `common.blocked`

### Dashboard
- `dashboard.title`, `dashboard.description`
- `dashboard.totalStudents`, `dashboard.totalTeachers`, `dashboard.totalCourses`
- `dashboard.enrollments`, `dashboard.pendingRequests`
- `dashboard.faculties`, `dashboard.departments`
- `dashboard.recentActivity`, `dashboard.quickStats`
- `dashboard.studentAttendance`, `dashboard.courseCompletion`, `dashboard.facultyUtilization`

### Sidebar
- `sidebar.dashboard`, `sidebar.students`, `sidebar.teachers`
- `sidebar.academicManagement`, `sidebar.curriculumPlanning`, `sidebar.administration`
- `sidebar.educationPlans`, `sidebar.curriculum`, `sidebar.academicSchedule`
- `sidebar.requests`, `sidebar.studentOrders`, `sidebar.organization`
- `sidebar.settings`, `sidebar.search`, `sidebar.analytics`

### Settings
- `settings.title`, `settings.description`
- `settings.appearance`, `settings.theme`, `settings.language`
- `settings.notifications`, `settings.saved`

### Profile
- `profile.title`, `profile.description`
- `profile.firstName`, `profile.lastName`, `profile.email`

## Next Steps to Complete

### Remaining Pages to Translate:
1. Teachers page (`/dashboard/teachers`)
2. Students page (`/dashboard/students`)
3. Curriculum page (`/dashboard/curriculum`)
4. Student Groups page (`/dashboard/student-groups`)
5. Evaluation System page
6. Academic Schedule page
7. Class Schedule page
8. Requests page
9. Student Orders page
10. Organizations page

### Remaining Endpoints to Update:
1. Students endpoint - Add lang parameter
2. Curriculum endpoint - Add lang parameter for course names
3. Student Groups endpoint - Add lang parameter
4. Evaluation System endpoint
5. Academic Schedule endpoint
6. Class Schedule endpoint

### Pattern to Follow:

**For Each Page**:
1. Import `useLanguage` hook
2. Replace hardcoded text with `t('key')`
3. Send `lang` parameter in API calls
4. Add `useEffect` dependency on `language` to refetch data

**For Each Backend Endpoint**:
1. Add `lang: str = Query('en', regex='^(en|ru|az)$')` parameter
2. Use `COALESCE(field->>%s, field->>'en', field->>'az')` for JSONB fields
3. Return localized fields in response

## Testing Checklist

- [x] User can change language in settings
- [x] Language saves to database
- [x] Language persists after logout/login
- [x] Dashboard UI updates when language changes
- [x] Dashboard data refetches with new language
- [x] Sidebar updates when language changes
- [x] Settings page updates when language changes
- [ ] All pages update when language changes
- [ ] All backend endpoints return localized data
- [ ] Test with user who has no preferences record
- [ ] Test with invalid language parameter
- [ ] Test offline (localStorage fallback)

## Benefits Achieved

1. ✅ **User-Specific**: Each user has their own language preference
2. ✅ **Persistent**: Language saved in database, survives logout
3. ✅ **Centralized**: Single source of truth for translations
4. ✅ **Type-Safe**: TypeScript ensures translation keys exist
5. ✅ **Fallback**: Graceful degradation if backend unavailable
6. ✅ **Real-time**: UI updates immediately on language change
7. ✅ **Database-Aware**: Backend returns language-specific JSONB fields
8. ✅ **Scalable**: Easy to add new languages or translation keys

## Architecture Decisions

### Why Backend-First Approach?
- User language preference is part of user profile
- Should be accessible across devices
- Allows analytics on language usage
- Supports future features (email notifications in user's language)

### Why JSONB for Localization?
- PostgreSQL native support
- Flexible schema
- Efficient indexing
- Easy to query with `->` and `->>`operators

### Why Context API?
- No external dependencies
- Type-safe with TypeScript
- React-native solution
- Lightweight and performant

## Performance Considerations

1. **Caching**: LanguageContext only fetches preferences once on mount
2. **Lazy Loading**: Translations loaded in same bundle as context
3. **Minimal Re-renders**: Only components using `t()` re-render on language change
4. **Efficient Queries**: JSONB queries use GIN indexes where available
5. **Fallback Chain**: Reduces failed lookups with en → az fallbacks

## Security Notes

- Language parameter validated with regex: `^(en|ru|az)$`
- Prevents injection attacks via language parameter
- User preferences require authentication (JWT token)
- No PII exposed in language settings

## Conclusion

The language system is now fully integrated with:
- ✅ Backend persistence per user
- ✅ Automatic loading on login
- ✅ Real-time UI updates
- ✅ Database content localization
- ✅ 3 languages supported (en, ru, az)
- ✅ 80+ translation keys
- ✅ 5 backend endpoints language-aware
- ✅ 4 frontend pages translated

**Status**: Core implementation complete. Remaining work is extending the pattern to all pages and endpoints following the established conventions.
