# Fix Delivery Server (Port 3022) - Troubleshooting Script
# This script diagnoses and fixes common issues with the delivery app server

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Delivery App Server Diagnostic Tool  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if port 3022 is in use
Write-Host "[1/5] Checking port 3022..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 3022 -ErrorAction SilentlyContinue
if ($portInUse) {
    $processId = $portInUse[0].OwningProcess
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    Write-Host "  [OK] Port 3022 is in use by process: $($process.ProcessName) (PID: $processId)" -ForegroundColor Green
    
    # Test if server responds
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3022" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "  [OK] Server is responding! Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host ""
        Write-Host "SUCCESS: Server is running correctly!" -ForegroundColor Green
        Write-Host "  Open in browser: http://localhost:3022" -ForegroundColor Cyan
        exit 0
    } catch {
        Write-Host "  [ERROR] Server is running but not responding properly" -ForegroundColor Red
        Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "  -> Will restart the server..." -ForegroundColor Yellow
        Stop-Process -Id $processId -Force
        Start-Sleep -Seconds 2
    }
} else {
    Write-Host "  [ERROR] Port 3022 is not in use" -ForegroundColor Red
}

# Step 2: Check if node_modules exists
Write-Host ""
Write-Host "[2/5] Checking dependencies..." -ForegroundColor Yellow
$frontendPath = "C:\Users\sanvi\Desktop\new\frontend"
if (Test-Path "$frontendPath\node_modules") {
    Write-Host "  [OK] node_modules found" -ForegroundColor Green
} else {
    Write-Host "  [WARN] node_modules not found. Installing dependencies..." -ForegroundColor Yellow
    Set-Location $frontendPath
    npm install
}

# Step 3: Check if delivery app files exist
Write-Host ""
Write-Host "[3/5] Checking delivery app files..." -ForegroundColor Yellow
$requiredFiles = @(
    "$frontendPath\apps\delivery\index.html",
    "$frontendPath\apps\delivery\src\main.tsx",
    "$frontendPath\apps\delivery\vite.config.ts"
)
$allFilesExist = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  [OK] $(Split-Path $file -Leaf)" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Missing: $(Split-Path $file -Leaf)" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Host ""
    Write-Host "ERROR: Required files are missing!" -ForegroundColor Red
    Write-Host "  Please ensure the delivery app is properly set up." -ForegroundColor Yellow
    exit 1
}

# Step 4: Kill any conflicting processes
Write-Host ""
    Write-Host "[4/5] Cleaning up old processes..." -ForegroundColor Yellow
$oldProcesses = Get-NetTCPConnection -LocalPort 3022 -ErrorAction SilentlyContinue
if ($oldProcesses) {
    foreach ($conn in $oldProcesses) {
        $pid = $conn.OwningProcess
        Write-Host "  -> Stopping process $pid..." -ForegroundColor Yellow
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
    Write-Host "  [OK] Cleanup complete" -ForegroundColor Green
} else {
    Write-Host "  [OK] No cleanup needed" -ForegroundColor Green
}

# Step 5: Start the server
Write-Host ""
Write-Host "[5/5] Starting delivery server..." -ForegroundColor Yellow
Set-Location $frontendPath

Write-Host "  -> Launching Vite dev server on port 3022..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev:delivery" -WorkingDirectory $frontendPath

Write-Host ""
Write-Host "Waiting for server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Verify server is running
$verification = Get-NetTCPConnection -LocalPort 3022 -ErrorAction SilentlyContinue
if ($verification) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  SERVER STARTED SUCCESSFULLY!        " -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  URL: http://localhost:3022" -ForegroundColor Cyan
    Write-Host "  Check the new PowerShell window for server logs" -ForegroundColor Yellow
    Write-Host ""
    
    # Opening the browser interactively can cause parsing issues in some shells.
    # To keep the script non-interactive and robust, automatically open the URL.
    try {
        Start-Process "http://localhost:3022" | Out-Null
    } catch {
        # Ignore if Start-Process cannot open a browser (e.g., server environments)
    }
} else {
    Write-Host ""
    Write-Host "ERROR: Server failed to start" -ForegroundColor Red
    Write-Host "  Check the PowerShell window for error messages" -ForegroundColor Yellow
}
