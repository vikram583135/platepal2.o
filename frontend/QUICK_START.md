# Quick Start Guide - Frontend Apps

## Port Configuration

- **Customer App**: Port 3020
- **Restaurant App**: Port 3021  
- **Delivery App**: Port 3022
- **Admin App**: Port 3023

## How to Start Each App

### Step 1: Navigate to frontend directory
```powershell
cd frontend
```

### Step 2: Start the app you need

**For Customer App (Port 3020):**
```powershell
npm run dev:customer
```
Then open: http://localhost:3020

**For Restaurant App (Port 3021):**
```powershell
npm run dev:restaurant
```
Then open: http://localhost:3021

**For Delivery App (Port 3022):**
```powershell
npm run dev:delivery
```

**For Admin App (Port 3023):**
```powershell
npm run dev:admin
```

## Test Credentials

### Customer App (Port 3020)
- Email: `customer@platepal.com`
- Password: `customer123`

### Restaurant App (Port 3021)
- Email: `restaurant@platepal.com`
- Password: `restaurant123`

### Admin App (Port 3023)
- Email: `admin@platepal.com`
- Password: `admin123`

## Troubleshooting

### If wrong app is running on a port:

1. Stop all node processes:
```powershell
Get-Process node | Stop-Process -Force
```

2. Start the correct app using the commands above

### Verify which app is running:

Check the browser tab title:
- Customer App: "PlatePal - Order Food Online"
- Restaurant App: "PlatePal - Restaurant Portal"

## Using the Helper Script

You can also use the PowerShell helper script:
```powershell
cd.\start-servers.ps1 frontend

```

This will give you a menu to select which app to start.

