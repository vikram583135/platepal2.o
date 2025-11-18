# Admin Server Connection Fix Guide

## Quick Start

### Method 1: Use the Helper Script (Recommended)

```powershell
cd frontend
.\scripts\start-admin-server.ps1
```

This script will:
- Check prerequisites
- Kill any process using port 3023
- Install dependencies if needed
- Start the server

### Method 2: Manual Start

```powershell
cd frontend
npm run dev:admin
```

## Issues Fixed

### 1. TypeScript Compilation Errors
- ✅ Fixed ErrorBoundary.tsx React import
- ✅ Fixed import.meta.env.DEV usage
- ✅ Added @types/node for path module support
- ✅ Created tsconfig.json for admin app
- ✅ Fixed vite.config.ts to use proper __dirname

### 2. Missing Files
- ✅ Created useAdminSocket.ts (was empty)
- ✅ Removed duplicate UsersPage.tsx file

### 3. Configuration Issues
- ✅ Updated vite.config.ts with proper root and host settings
- ✅ Added tsconfig.json for admin app
- ✅ Updated tsconfig.node.json to include admin vite.config.ts

## Verification Steps

### Step 1: Check Port Availability
```powershell
Get-NetTCPConnection -LocalPort 3023 -ErrorAction SilentlyContinue
```
If port is in use, kill the process:
```powershell
Stop-Process -Id <PID> -Force
```

### Step 2: Verify Dependencies
```powershell
cd frontend
npm install
```

### Step 3: Check for Errors
```powershell
cd frontend
npm run type-check
```

### Step 4: Start Server
```powershell
cd frontend
npm run dev:admin
```

## Expected Output

When the server starts successfully, you should see:

```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:3023/
➜  Network: use --host to expose
➜  press h + enter to show help
```

## Troubleshooting

### Issue: "Cannot find module 'path'"
**Solution:** @types/node is now installed. If still seeing error, run:
```powershell
cd frontend
npm install --save-dev @types/node
```

### Issue: "Port 3023 already in use"
**Solution:** Use the helper script or manually kill the process:
```powershell
Get-NetTCPConnection -LocalPort 3023 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

### Issue: "Cannot find module ErrorBoundary"
**Solution:** Verify file exists:
```powershell
Test-Path frontend/apps/admin/src/components/ErrorBoundary.tsx
```

### Issue: "useAdminSocket is not a module"
**Solution:** File has been created. Verify:
```powershell
Test-Path frontend/apps/admin/src/hooks/useAdminSocket.ts
```

### Issue: Server starts but shows blank page
**Check:**
1. Browser console for errors (F12)
2. Network tab for failed requests
3. Verify backend is running on port 8000

### Issue: "Module not found" errors
**Solution:** Clear cache and reinstall:
```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
npm install
```

## Files Modified/Created

### Fixed Files
- `frontend/apps/admin/vite.config.ts` - Fixed path imports and added root/host
- `frontend/apps/admin/src/components/ErrorBoundary.tsx` - Fixed React import and env check
- `frontend/apps/admin/src/hooks/useAdminSocket.ts` - Created (was empty)
- `frontend/package.json` - Added @types/node
- `frontend/tsconfig.node.json` - Added node types and admin vite.config
- `frontend/apps/admin/tsconfig.json` - Created for admin app

### Removed Files
- `frontend/apps/admin/src/pages/UsersPage.tsx` - Duplicate file removed

### Created Scripts
- `frontend/scripts/check-admin-server.ps1` - Diagnostic script
- `frontend/scripts/start-admin-server.ps1` - Startup script

## Testing the Fix

1. **Start the server:**
   ```powershell
   cd frontend
   npm run dev:admin
   ```

2. **Open browser:**
   Navigate to `http://localhost:3023/`

3. **Expected result:**
   - Login page should load (if not authenticated)
   - Or dashboard should load (if authenticated)
   - No console errors
   - No 404 errors

## Still Having Issues?

1. Run the diagnostic script:
   ```powershell
   cd frontend
   .\scripts\check-admin-server.ps1
   ```

2. Check terminal output for specific error messages

3. Verify all files from the fix are present

4. Check browser console (F12) for client-side errors

5. Verify backend server is running on port 8000

