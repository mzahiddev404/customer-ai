# Starting the Application

## Issue: Frontend Turbopack Permission Error

The frontend has a macOS permission issue with Turbopack trying to read the Desktop directory. This is a known Next.js 16 issue.

## Solutions

### Option 1: Grant Terminal Full Disk Access (Recommended)

1. Go to **System Preferences** → **Security & Privacy** → **Privacy** → **Full Disk Access**
2. Add Terminal (or your terminal app) to the list
3. Restart Terminal
4. Then run the frontend

### Option 2: Run Frontend Manually

Open a new terminal and run:

```bash
cd customer-ai/frontend
export NEXT_PUBLIC_API_URL=http://localhost:8001
npm run dev
```

### Option 3: Use the Start Script

```bash
cd customer-ai/frontend
./start-frontend.sh
```

## Current Setup

- **Backend**: Running on **port 8001** (not 8000 because another service uses 8000)
- **Frontend**: Should run on **port 3000**
- **API URL**: Frontend is configured to use `http://localhost:8001`

## Quick Start Commands

**Terminal 1 - Backend:**
```bash
cd customer-ai/backend/app
source ../../.venv/bin/activate
uvicorn main:app --reload --port 8001
```

**Terminal 2 - Frontend:**
```bash
cd customer-ai/frontend
export NEXT_PUBLIC_API_URL=http://localhost:8001
npm run dev
```

## Verify It's Working

- Backend Health: http://localhost:8001/health
- Frontend: http://localhost:3000
- API Docs: http://localhost:8001/docs

