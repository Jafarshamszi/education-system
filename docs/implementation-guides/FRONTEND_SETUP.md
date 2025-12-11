# Frontend Setup Guide

## Folder Structure

```
Education-system/
├── frontend/              # Admin/Rector/Dean Portal (Port 3000)
├── frontend-teacher/      # Teacher Portal (Port 3001)
└── frontend-student/      # Student Portal (Port 3002)
```

## Running Frontends

### Option 1: Individual Terminals

**Admin Frontend (Port 3000):**
```bash
cd /home/axel/Developer/Education-system/frontend
bun dev
# or
bun run dev
```

**Teacher Frontend (Port 3001):**
```bash
cd /home/axel/Developer/Education-system/frontend-teacher
bun dev
# or
bun run dev
```

**Student Frontend (Port 3002):**
```bash
cd /home/axel/Developer/Education-system/frontend-student
bun dev
# or
bun run dev
```

### Option 2: Using the Start Script

```bash
# From project root
./start-frontends.sh
```

## Access URLs

- **Admin Portal:** http://localhost:3000
- **Teacher Portal:** http://localhost:3001
- **Student Portal:** http://localhost:3002

## Login Pages

- **Admin:** http://localhost:3000/login
- **Teacher:** http://localhost:3001/login
- **Student:** http://localhost:3002/login

## Package Manager

All frontends use **Bun** as the package manager:

```bash
# Install dependencies
bun install

# Add new package
bun add [package-name]

# Remove package
bun remove [package-name]

# Run scripts
bun dev
bun build
bun start
```

## Troubleshooting

### "Command not found: bun"

Install Bun:
```bash
curl -fsSL https://bun.sh/install | bash
```

### Port already in use

Check what's using the port:
```bash
lsof -i :3000  # or 3001, 3002
```

Kill the process:
```bash
kill -9 [PID]
```

### Dependencies issues

Reinstall dependencies:
```bash
cd frontend  # or frontend-teacher, frontend-student
rm -rf node_modules bun.lock
bun install
```

## Building for Production

```bash
# Build each frontend
cd frontend && bun run build
cd ../frontend-teacher && bun run build
cd ../frontend-student && bun run build

# Start production servers
cd frontend && bun run start &  # Port 3000
cd ../frontend-teacher && bun run start &  # Port 3001
cd ../frontend-student && bun run start &  # Port 3002
```

## Adding New shadcn Components

```bash
# In any frontend
cd [frontend-folder]
bunx --bun shadcn@latest add [component-name]

# Examples:
bunx --bun shadcn@latest add button
bunx --bun shadcn@latest add card
bunx --bun shadcn@latest add table
bunx --bun shadcn@latest add dashboard-01
```

## Available shadcn Blocks

```bash
# Login blocks
login-01, login-02, login-03, login-04

# Dashboard blocks
dashboard-01, dashboard-02, dashboard-03, dashboard-04, dashboard-05

# Sidebar blocks
sidebar-01, sidebar-02, sidebar-03, sidebar-04, sidebar-05, sidebar-06, sidebar-07

# Other blocks
table, calendar, chart, form, dialog, sheet, toast, etc.
```

## Development Workflow

1. **Start Backend:**
   ```bash
   cd backend
   source /home/axel/Developer/Education-system/.venv/bin/activate
   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

2. **Start Frontend(s):**
   ```bash
   # Open new terminals for each
   cd frontend && bun dev
   cd frontend-teacher && bun dev
   cd frontend-student && bun dev
   ```

3. **Access Application:**
   - Admin: http://localhost:3000
   - Teacher: http://localhost:3001
   - Student: http://localhost:3002

## Notes

- All frontends use the same backend API (port 8000)
- CORS is configured for ports 3000, 3001, 3002
- Each frontend has independent dependencies
- Shared authentication via JWT tokens
- Different themes/branding per portal

---

**Last Updated:** October 11, 2025
