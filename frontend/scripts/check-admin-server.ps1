# Admin Server Diagnostic Script
# This script checks all prerequisites for starting the admin server

Write-Host "Admin Server Diagnostic Tool" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host ""

$errors = @()
$warnings = @()

# Check 1: Verify we're in the right directory
Write-Host "1. Checking working directory..." -ForegroundColor Yellow
if (Test-Path "package.json") {
    Write-Host "   ✓ package.json found" -ForegroundColor Green
} else {
    $errors += "package.json not found. Please run from frontend directory."
    Write-Host "   ✗ package.json not found" -ForegroundColor Red
}

# Check 2: Verify node_modules exists
Write-Host "2. Checking node_modules..." -ForegroundColor Yellow
if (Test-Path "node_modules") {
    Write-Host "   ✓ node_modules exists" -ForegroundColor Green
} else {
    $errors += "node_modules not found. Run 'npm install' first."
    Write-Host "   ✗ node_modules not found" -ForegroundColor Red
}

# Check 3: Verify admin app structure
Write-Host "3. Checking admin app structure..." -ForegroundColor Yellow
$requiredFiles = @(
    "apps/admin/vite.config.ts",
    "apps/admin/index.html",
    "apps/admin/src/main.tsx",
    "apps/admin/src/App.tsx",
    "apps/admin/src/components/ErrorBoundary.tsx"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "   ✓ $file" -ForegroundColor Green
    } else {
        $errors += "Required file missing: $file"
        Write-Host "   ✗ $file" -ForegroundColor Red
    }
}

# Check 4: Verify CSS file exists
Write-Host "4. Checking CSS import..." -ForegroundColor Yellow
if (Test-Path "apps/customer/src/index.css") {
    Write-Host "   ✓ CSS file exists" -ForegroundColor Green
} else {
    $warnings += "CSS file not found at apps/customer/src/index.css"
    Write-Host "   ⚠ CSS file not found" -ForegroundColor Yellow
}

# Check 5: Check port 3023 availability
Write-Host "5. Checking port 3023..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 3023 -ErrorAction SilentlyContinue
if ($portInUse) {
    $processId = $portInUse.OwningProcess
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    $warnings += "Port 3023 is in use by process: $processId ($($process.ProcessName))"
    Write-Host "   ⚠ Port 3023 is in use by PID: $processId" -ForegroundColor Yellow
} else {
    Write-Host "   ✓ Port 3023 is available" -ForegroundColor Green
}

# Check 6: Verify npm script exists
Write-Host "6. Checking npm scripts..." -ForegroundColor Yellow
$packageJson = Get-Content "package.json" | ConvertFrom-Json
if ($packageJson.scripts.'dev:admin') {
    Write-Host "   ✓ dev:admin script exists" -ForegroundColor Green
    Write-Host "      Command: $($packageJson.scripts.'dev:admin')" -ForegroundColor Gray
} else {
    $errors += "dev:admin script not found in package.json"
    Write-Host "   ✗ dev:admin script not found" -ForegroundColor Red
}

# Check 7: Check for duplicate files
Write-Host "7. Checking for duplicate files..." -ForegroundColor Yellow
if (Test-Path "apps/admin/src/pages/UsersPage.tsx") {
    if (Test-Path "apps/admin/src/pages/Users/UsersPage.tsx") {
        $warnings += "Duplicate UsersPage.tsx files found. This may cause import issues."
        Write-Host "   ⚠ Duplicate UsersPage.tsx files found" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ✓ No duplicate UsersPage files" -ForegroundColor Green
}

# Summary
Write-Host ""
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "=======" -ForegroundColor Cyan

if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "✓ All checks passed! You can start the server with: npm run dev:admin" -ForegroundColor Green
} else {
    if ($errors.Count -gt 0) {
        Write-Host ""
        Write-Host "Errors (must fix):" -ForegroundColor Red
        foreach ($error in $errors) {
            Write-Host "  ✗ $error" -ForegroundColor Red
        }
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host ""
        Write-Host "Warnings:" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "  ⚠ $warning" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "To start the admin server:" -ForegroundColor Cyan
Write-Host "  npm run dev:admin" -ForegroundColor White

