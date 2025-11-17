# Script to Allow Node.js and HTTPS Through Windows Firewall
# Run this script as Administrator

Write-Host "=== Configuring Windows Firewall for TestSprite ===" -ForegroundColor Cyan

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host ""
    Write-Host "This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
    pause
    exit
}

Write-Host ""
Write-Host "Running as Administrator" -ForegroundColor Green

# Find Node.js path
Write-Host ""
Write-Host "1. Finding Node.js installation..." -ForegroundColor Yellow
try {
    $nodePath = (Get-Command node).Source
    Write-Host "   Found Node.js at: $nodePath" -ForegroundColor Green
} catch {
    Write-Host "   Node.js not found in PATH" -ForegroundColor Red
    Write-Host "   Please install Node.js or add it to PATH" -ForegroundColor Yellow
    pause
    exit
}

# Check if rule already exists
$existingRule = Get-NetFirewallRule -DisplayName "Node.js - Outbound HTTPS" -ErrorAction SilentlyContinue

if ($existingRule) {
    Write-Host ""
    Write-Host "2. Firewall rule already exists. Removing old rule..." -ForegroundColor Yellow
    Remove-NetFirewallRule -DisplayName "Node.js - Outbound HTTPS" -ErrorAction SilentlyContinue
    Write-Host "   Old rule removed" -ForegroundColor Green
}

# Create firewall rule for Node.js
Write-Host ""
Write-Host "3. Creating firewall rule for Node.js..." -ForegroundColor Yellow
try {
    $params = @{
        DisplayName = "Node.js - Outbound HTTPS"
        Direction = "Outbound"
        Program = $nodePath
        Action = "Allow"
        Protocol = "TCP"
        RemotePort = 443
        Profile = "Any"
        Description = "Allow Node.js to make outbound HTTPS connections for TestSprite"
        ErrorAction = "Stop"
    }
    New-NetFirewallRule @params
    
    Write-Host "   Firewall rule created successfully!" -ForegroundColor Green
} catch {
    Write-Host "   Failed to create firewall rule: $_" -ForegroundColor Red
    pause
    exit
}

# Create general HTTPS outbound rule (optional, more permissive)
Write-Host ""
Write-Host "4. Creating general HTTPS outbound rule..." -ForegroundColor Yellow
$generalRule = Get-NetFirewallRule -DisplayName "Allow Outbound HTTPS (Port 443)" -ErrorAction SilentlyContinue

if (-not $generalRule) {
    try {
        $generalParams = @{
            DisplayName = "Allow Outbound HTTPS (Port 443)"
            Direction = "Outbound"
            Action = "Allow"
            Protocol = "TCP"
            RemotePort = 443
            Profile = "Any"
            Description = "Allow outbound HTTPS connections on port 443"
            ErrorAction = "Stop"
        }
        New-NetFirewallRule @generalParams
        
        Write-Host "   General HTTPS rule created!" -ForegroundColor Green
    } catch {
        Write-Host "   Could not create general rule (may already exist): $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "   General HTTPS rule already exists" -ForegroundColor Green
}

# Test connectivity
Write-Host ""
Write-Host "5. Testing connectivity to TestSprite..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
$testResult = Test-NetConnection -ComputerName 3.215.168.52 -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue

if ($testResult) {
    Write-Host "   Connection successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Firewall configuration complete! You can now run TestSprite tests." -ForegroundColor Green
} else {
    Write-Host "   Connection still failing" -ForegroundColor Red
    Write-Host ""
    Write-Host "The firewall rule was created, but connection still fails." -ForegroundColor Yellow
    Write-Host "   This may indicate:" -ForegroundColor Yellow
    Write-Host "   - Network connectivity issues" -ForegroundColor Yellow
    Write-Host "   - TestSprite service may be down" -ForegroundColor Yellow
    Write-Host "   - Corporate firewall blocking the connection" -ForegroundColor Yellow
    Write-Host "   - Antivirus software blocking the connection" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Configuration Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
