# Admin Server Setup Verification Script
# Run this to verify everything is set up correctly

Write-Host "Admin Server Setup Verification" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendPath = Split-Path -Parent $scriptPath

Set-Location $frontendPath

# Check 1: Required files exist
Write-Host "1. Checking required files..." -ForegroundColor Yellow
$requiredFiles = @(
    "apps/admin/vite.config.ts",
    "apps/admin/index.html",
    "apps/admin/src/main.tsx",
    "apps/admin/src/App.tsx",
    "apps/admin/src/components/ErrorBoundary.tsx",
    "apps/admin/src/hooks/useAdminSocket.ts",
    "apps/admin/tsconfig.json"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "   ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "   ✗ MISSING: $file" -ForegroundColor Red
        $allGood = $false
    }
}

# Check 2: No duplicate files
Write-Host ""
Write-Host "2. Checking for duplicate files..." -ForegroundColor Yellow
if (Test-Path "apps/admin/src/pages/UsersPage.tsx") {
    Write-Host "   ✗ Duplicate UsersPage.tsx found - should be removed" -ForegroundColor Red
    $allGood = $false
} else {
    Write-Host "   ✓ No duplicate UsersPage.tsx" -ForegroundColor Green
}

# Check 3: Dependencies
Write-Host ""
Write-Host "3. Checking dependencies..." -ForegroundColor Yellow
if (Test-Path "node_modules") {
    Write-Host "   ✓ node_modules exists" -ForegroundColor Green
    
    if (Test-Path "node_modules\@types\node") {
        Write-Host "   ✓ @types/node installed" -ForegroundColor Green
    } else {
        Write-Host "   ✗ @types/node missing - run: npm install --save-dev @types/node" -ForegroundColor Red
        $allGood = $false
    }
} else {
    Write-Host "   ✗ node_modules missing - run: npm install" -ForegroundColor Red
    $allGood = $false
}

# Check 4: Port availability
Write-Host ""
Write-Host "4. Checking port 3023..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 3023 -ErrorAction SilentlyContinue
if ($portInUse) {
    $pid = $portInUse.OwningProcess
    Write-Host "   ⚠ Port 3023 in use by PID: $pid" -ForegroundColor Yellow
    Write-Host "      Run: Stop-Process -Id $pid -Force" -ForegroundColor Gray
} else {
    Write-Host "   ✓ Port 3023 is available" -ForegroundColor Green
}

# Check 5: TypeScript config
Write-Host ""
Write-Host "5. Checking TypeScript configuration..." -ForegroundColor Yellow
if (Test-Path "apps/admin/tsconfig.json") {
    Write-Host "   ✓ Admin tsconfig.json exists" -ForegroundColor Green
} else {
    Write-Host "   ✗ Admin tsconfig.json missing" -ForegroundColor Red
    $allGood = $false
}

# Check 6: Vite config syntax
Write-Host ""
Write-Host "6. Checking vite.config.ts..." -ForegroundColor Yellow
$viteConfig = Get-Content "apps/admin/vite.config.ts" -Raw
if ($viteConfig -match "port:\s*3023") {
    Write-Host "   ✓ Port 3023 configured" -ForegroundColor Green
} else {
    Write-Host "   ⚠ Port configuration may be incorrect" -ForegroundColor Yellow
}

if ($viteConfig -match "root:\s*__dirname") {
    Write-Host "   ✓ Root directory configured" -ForegroundColor Green
} else {
    Write-Host "   ⚠ Root directory may not be configured" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "=======" -ForegroundColor Cyan

if ($allGood) {
    Write-Host "✓ All checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To start the server:" -ForegroundColor Cyan
    Write-Host "  npm run dev:admin" -ForegroundColor White
    Write-Host ""
    Write-Host "Or use the helper script:" -ForegroundColor Cyan
    Write-Host "  .\scripts\start-admin-server.ps1" -ForegroundColor White
} else {
    Write-Host "✗ Some issues found. Please fix them before starting the server." -ForegroundColor Red
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "  - Install dependencies: npm install" -ForegroundColor White
    Write-Host "  - Install @types/node: npm install --save-dev @types/node" -ForegroundColor White
    Write-Host "  - Remove duplicate files if any" -ForegroundColor White
}

