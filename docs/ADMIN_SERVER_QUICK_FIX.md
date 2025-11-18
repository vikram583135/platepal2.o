# Admin Server Quick Fix - Step by Step

## If you're getting 404 on localhost:3023, follow these steps:

### Step 1: Kill any process using port 3023
```powershell
Get-NetTCPConnection -LocalPort 3023 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

### Step 2: Navigate to frontend directory
```powershell
cd frontend
```

### Step 3: Install/Update dependencies
```powershell
npm install
```

### Step 4: Verify setup (optional)
```powershell
.\scripts\verify-admin-setup.ps1
```

### Step 5: Start the server
```powershell
npm run dev:admin
```

### Step 6: Open browser
Navigate to: `http://localhost:3023/`

## What Was Fixed

1. **TypeScript Errors:**
   - Fixed ErrorBoundary React import
   - Fixed import.meta.env usage
   - Added @types/node for path module

2. **Missing Files:**
   - Created useAdminSocket.ts (was empty)
   - Removed duplicate UsersPage.tsx

3. **Configuration:**
   - Fixed vite.config.ts with proper __dirname
   - Added tsconfig.json for admin app
   - Updated tsconfig.node.json

4. **Dependencies:**
   - Added @types/node to package.json

## One-Command Fix

If you want to do everything at once:

```powershell
cd frontend; Get-NetTCPConnection -LocalPort 3023 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }; npm install; npm run dev:admin
```

## Still Not Working?

1. Check terminal output for specific errors
2. Run: `.\scripts\check-admin-server.ps1`
3. Verify backend is running on port 8000
4. Check browser console (F12) for errors

