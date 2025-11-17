# Firewall and Proxy Settings Guide for TestSprite

This guide will help you configure Windows Firewall and proxy settings to allow TestSprite to connect to its cloud service.

## Step 1: Check Windows Firewall Settings

### Method 1: Using Windows Security (Recommended)

1. **Open Windows Security**:
   - Press `Windows Key + I` to open Settings
   - Go to **Privacy & Security** → **Windows Security**
   - Click **Firewall & network protection**

2. **Check Firewall Status**:
   - Ensure Windows Defender Firewall is **ON** for all networks (Domain, Private, Public)
   - If it's off, turn it on

3. **Allow an App Through Firewall**:
   - Click **Allow an app through firewall** (or **Advanced settings**)
   - Click **Change settings** (requires admin)
   - Look for **Node.js** or **npm** in the list
   - If found, ensure both **Private** and **Public** are checked
   - If not found, click **Allow another app...**
   - Browse to: `C:\Program Files\nodejs\node.exe` (or where Node.js is installed)
   - Add it and check both **Private** and **Public**

### Method 2: Using Command Line (PowerShell as Administrator)

1. **Open PowerShell as Administrator**:
   - Right-click Start menu → **Windows PowerShell (Admin)** or **Terminal (Admin)**
   - Or search for "PowerShell" → Right-click → **Run as administrator**

2. **Check Firewall Status**:
   ```powershell
   Get-NetFirewallProfile | Select-Object Name, Enabled
   ```

3. **Allow Node.js Through Firewall** (if needed):
   ```powershell
   # Find Node.js installation path
   $nodePath = (Get-Command node).Source
   Write-Host "Node.js path: $nodePath"
   
   # Allow Node.js through firewall
   New-NetFirewallRule -DisplayName "Node.js - Outbound HTTPS" `
       -Direction Outbound `
       -Program $nodePath `
       -Action Allow `
       -Protocol TCP `
       -RemotePort 443 `
       -Profile Any
   ```

4. **Allow Outbound HTTPS (Port 443) for All Apps** (if needed):
   ```powershell
   New-NetFirewallRule -DisplayName "Allow Outbound HTTPS" `
       -Direction Outbound `
       -Action Allow `
       -Protocol TCP `
       -RemotePort 443 `
       -Profile Any
   ```

## Step 2: Check Proxy Settings

### Check if Proxy is Configured

1. **Open Settings**:
   - Press `Windows Key + I`
   - Go to **Network & Internet** → **Proxy**

2. **Check Proxy Configuration**:
   - Look at **Automatic proxy setup** and **Manual proxy setup**
   - If a proxy is configured, you may need to:
     - Add TestSprite domains to proxy exceptions
     - Or configure Node.js to use the proxy

3. **Check System Proxy Environment Variables**:
   ```powershell
   # Check current proxy settings
   $env:HTTP_PROXY
   $env:HTTPS_PROXY
   $env:NO_PROXY
   ```

### Configure Node.js to Use Proxy (if needed)

If you have a corporate proxy, you may need to configure npm/Node.js:

```powershell
# Set proxy (replace with your proxy details)
npm config set proxy http://proxy.company.com:8080
npm config set https-proxy http://proxy.company.com:8080

# Or set environment variables
$env:HTTP_PROXY = "http://proxy.company.com:8080"
$env:HTTPS_PROXY = "http://proxy.company.com:8080"
```

## Step 3: Test Network Connectivity

### Test Connection to TestSprite Service

Run these commands in PowerShell to test connectivity:

```powershell
# Test basic connectivity
Test-NetConnection -ComputerName 3.215.168.52 -Port 443

# Test with detailed information
Test-NetConnection -ComputerName 3.215.168.52 -Port 443 -InformationLevel Detailed

# Test DNS resolution
Resolve-DnsName 3.215.168.52

# Test HTTPS connection
Invoke-WebRequest -Uri "https://3.215.168.52" -Method GET -TimeoutSec 10
```

### Test from Node.js

```powershell
# Test using Node.js
node -e "const https = require('https'); https.get('https://3.215.168.52', (res) => { console.log('Status:', res.statusCode); }).on('error', (e) => { console.error('Error:', e.message); });"
```

## Step 4: Check Antivirus Software

Some antivirus software may block outbound connections:

1. **Check Windows Defender**:
   - Windows Security → **Virus & threat protection**
   - Check if any threats are blocked

2. **Check Third-Party Antivirus**:
   - If you have other antivirus (Norton, McAfee, etc.), check their firewall settings
   - Temporarily disable to test (remember to re-enable)

## Step 5: Check Corporate Network/VPN

If you're on a corporate network or VPN:

1. **Corporate Firewall**:
   - Contact IT to whitelist TestSprite domains/IPs:
     - `3.215.168.52`
     - `3.234.173.53`
     - Port: `443` (HTTPS)

2. **VPN Settings**:
   - Some VPNs block certain connections
   - Try disconnecting VPN temporarily to test
   - Or configure VPN to allow these connections

## Step 6: Quick Diagnostic Script

Run this PowerShell script to diagnose the issue:

```powershell
Write-Host "=== Network Diagnostic for TestSprite ===" -ForegroundColor Cyan

# Check Node.js
Write-Host "`n1. Checking Node.js..." -ForegroundColor Yellow
$nodeVersion = node --version
Write-Host "   Node.js version: $nodeVersion" -ForegroundColor Green

# Check Firewall
Write-Host "`n2. Checking Windows Firewall..." -ForegroundColor Yellow
$firewallStatus = Get-NetFirewallProfile | Select-Object Name, Enabled
$firewallStatus | Format-Table

# Check Proxy
Write-Host "`n3. Checking Proxy Settings..." -ForegroundColor Yellow
$proxy = Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
Write-Host "   Proxy Enable: $($proxy.ProxyEnable)"
if ($proxy.ProxyEnable -eq 1) {
    Write-Host "   Proxy Server: $($proxy.ProxyServer)" -ForegroundColor Yellow
}

# Test Connectivity
Write-Host "`n4. Testing Connectivity to TestSprite..." -ForegroundColor Yellow
$testResult = Test-NetConnection -ComputerName 3.215.168.52 -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($testResult) {
    Write-Host "   ✓ Connection successful!" -ForegroundColor Green
} else {
    Write-Host "   ✗ Connection failed" -ForegroundColor Red
    Write-Host "   This indicates a firewall or network issue." -ForegroundColor Yellow
}

# Check DNS
Write-Host "`n5. Checking DNS..." -ForegroundColor Yellow
try {
    $dns = Resolve-DnsName 3.215.168.52 -ErrorAction Stop
    Write-Host "   ✓ DNS resolution works" -ForegroundColor Green
} catch {
    Write-Host "   ✗ DNS resolution failed" -ForegroundColor Red
}

Write-Host "`n=== Diagnostic Complete ===" -ForegroundColor Cyan
```

## Step 7: Temporary Workaround (For Testing Only)

If you need to test immediately and can't change firewall settings:

1. **Temporarily Disable Firewall** (NOT RECOMMENDED for production):
   ```powershell
   # Run as Administrator
   Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False
   ```

2. **Re-enable Firewall After Testing**:
   ```powershell
   Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True
   ```

⚠️ **Warning**: Only disable firewall temporarily for testing. Re-enable it immediately after.

## Step 8: Retry TestSprite After Configuration

After making changes:

1. **Close and reopen PowerShell/Terminal**
2. **Retry TestSprite test execution**:
   ```powershell
   cd C:\Users\sanvi\Desktop\new
   node C:\Users\sanvi\AppData\Local\npm-cache\_npx\8ddf6bea01b2519d\node_modules\@testsprite\testsprite-mcp\dist\index.js generateCodeAndExecute
   ```

## Common Issues and Solutions

### Issue: "Connection Timeout"
- **Solution**: Firewall is blocking outbound HTTPS. Follow Step 1 to allow it.

### Issue: "Proxy Error"
- **Solution**: Configure proxy settings (Step 2) or add TestSprite to proxy exceptions.

### Issue: "DNS Resolution Failed"
- **Solution**: Check DNS settings or use a different DNS server (e.g., 8.8.8.8).

### Issue: "Certificate Error"
- **Solution**: This is usually OK for testing. TestSprite may use self-signed certificates.

## Need More Help?

If issues persist:
1. Check TestSprite documentation: https://docs.testsprite.com
2. Contact TestSprite support with your diagnostic results
3. Check if your organization has network restrictions

---

**Last Updated**: $(Get-Date -Format "yyyy-MM-dd")

