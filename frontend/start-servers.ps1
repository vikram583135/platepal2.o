# PlatePal Frontend Server Startup Script
# This script helps you start the correct apps on the correct ports

Write-Host "PlatePal Frontend Server Manager" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Check if ports are available
function Test-Port {
    param([int]$Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return $connection -eq $null
}

# Stop existing servers
Write-Host "Checking for existing servers..." -ForegroundColor Yellow
$ports = @(3020, 3021, 3022, 3023)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    $processIds = $connections | Where-Object {$_.OwningProcess -ne 0} | Select-Object -ExpandProperty OwningProcess -Unique
    if ($processIds) {
        foreach ($procId in $processIds) {
            Write-Host "Stopping process $procId on port $port" -ForegroundColor Red
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host ""
Write-Host "Available apps:" -ForegroundColor Green
Write-Host "  1. Customer App (Port 3020)"
Write-Host "  2. Restaurant App (Port 3021)"
Write-Host "  3. Delivery App (Port 3022)"
Write-Host "  4. Admin App (Port 3023)"
Write-Host "  5. Start All Apps"
Write-Host ""
$choice = Read-Host "Select app to start (1-5)"

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

switch ($choice) {
    "1" {
        Write-Host "Starting Customer App on port 3020..." -ForegroundColor Green
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; npm run dev:customer"
    }
    "2" {
        Write-Host "Starting Restaurant App on port 3021..." -ForegroundColor Green
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; npm run dev:restaurant"
    }
    "3" {
        Write-Host "Starting Delivery App on port 3022..." -ForegroundColor Green
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; npm run dev:delivery"
    }
    "4" {
        Write-Host "Starting Admin App on port 3023..." -ForegroundColor Green
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; npm run dev:admin"
    }
    "5" {
        Write-Host "Starting all apps..." -ForegroundColor Green
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; npm run dev:customer"
        Start-Sleep -Seconds 2
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; npm run dev:restaurant"
        Start-Sleep -Seconds 2
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; npm run dev:delivery"
        Start-Sleep -Seconds 2
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; npm run dev:admin"
    }
    default {
        Write-Host "Invalid choice!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Server(s) started! Check the new PowerShell windows." -ForegroundColor Green

