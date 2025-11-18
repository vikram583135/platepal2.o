# Admin Server Troubleshooting Guide

## Issue: 404 Error on localhost:3023

If you're seeing a 404 error when accessing `http://localhost:3023/`, the admin frontend server is not running.

## Quick Fix Steps

### 1. Start the Admin Server

Open a terminal in the `frontend` directory and run:

```bash
cd frontend
npm run dev:admin
```

You should see output like:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:3023/
➜  Network: use --host to expose
```

### 2. Check if Port 3023 is Already in Use

If you get an error about the port being in use:

**Windows PowerShell:**
```powershell
Get-NetTCPConnection -LocalPort 3023 | Select-Object -Property OwningProcess
```

**Kill the process:**
```powershell
Stop-Process -Id <PID> -Force
```

**Or use the helper script:**
```powershell
cd frontend
.\start-servers.ps1
# Select option 4 for Admin App
```

### 3. Verify Dependencies are Installed

Make sure all npm packages are installed:

```bash
cd frontend
npm install
```

### 4. Check for Compilation Errors

If the server starts but shows errors, check:

1. **TypeScript Errors:**
   ```bash
   npm run type-check
   ```

2. **Linting Errors:**
   ```bash
   npm run lint
   ```

### 5. Common Issues and Solutions

#### Issue: "Cannot find module" errors
**Solution:** Delete `node_modules` and reinstall:
```bash
cd frontend
rm -rf node_modules
npm install
```

#### Issue: "Port already in use"
**Solution:** Kill the process using port 3023 (see step 2)

#### Issue: "Vite config not found"
**Solution:** Verify `frontend/apps/admin/vite.config.ts` exists

#### Issue: "ErrorBoundary not found"
**Solution:** Verify `frontend/apps/admin/src/components/ErrorBoundary.tsx` exists

### 6. Verify Backend is Running

The admin dashboard requires the backend API to be running:

```bash
cd backend
python manage.py runserver
```

Backend should be accessible at `http://localhost:8000`

### 7. Check Browser Console

Open browser DevTools (F12) and check:
- Console tab for JavaScript errors
- Network tab for failed API requests
- Application tab for localStorage issues

### 8. Clear Browser Cache

Sometimes cached files cause issues:
- Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
- Or clear browser cache completely

## Verification Checklist

- [ ] Backend server running on port 8000
- [ ] Frontend admin server running on port 3023
- [ ] No TypeScript compilation errors
- [ ] No console errors in browser
- [ ] Dependencies installed (`npm install` completed)
- [ ] Port 3023 not blocked by firewall

## Still Having Issues?

1. Check the terminal output when running `npm run dev:admin`
2. Look for specific error messages
3. Verify all files from the fixes are present:
   - `frontend/apps/admin/src/components/ErrorBoundary.tsx`
   - `frontend/apps/admin/src/main.tsx` (with ErrorBoundary import)
   - All other modified files

## Expected Behavior

When the server starts successfully, you should:
1. See Vite dev server output in terminal
2. Be able to access `http://localhost:3023/` in browser
3. See the login page (if not authenticated) or dashboard (if authenticated)

