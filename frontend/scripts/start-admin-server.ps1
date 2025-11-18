# Admin Server Startup Script
# This script ensures all prerequisites are met before starting the server

Write-Host "Starting Admin Server..." -ForegroundColor Cyan
Write-Host "=======================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendPath = Split-Path -Parent $scriptPath

# Change to frontend directory
Set-Location $frontendPath

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "node_modules not found. Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install dependencies!" -ForegroundColor Red
        exit 1
    }
}

# Check port 3023
Write-Host "Checking port 3023..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 3023 -ErrorAction SilentlyContinue
if ($portInUse) {
    $processId = $portInUse.OwningProcess
    Write-Host "Port 3023 is in use by process $processId. Killing process..." -ForegroundColor Yellow
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Start the server
Write-Host ""
Write-Host "Starting admin server on port 3023..." -ForegroundColor Green
Write-Host "Server will be available at: http://localhost:3023" -ForegroundColor Cyan
Write-Host ""

npm run dev:admin

