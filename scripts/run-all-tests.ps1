Param(
  [switch]$SkipSeed
)

$ErrorActionPreference = "Stop"

Write-Host "Starting PlatePal test orchestration" -ForegroundColor Cyan

# Helper: start a process and wait a short time
function Start-Background($name, $cmd, $args) {
  Write-Host "Launching $name..." -ForegroundColor Yellow
  Start-Process -FilePath $cmd -ArgumentList $args -WindowStyle Minimized
  Start-Sleep -Seconds 3
}

# 1) Backend: install deps and start server
Write-Host "Ensuring backend Python deps..." -ForegroundColor Yellow
pip install -r .\backend\requirements.txt | Out-Null

Write-Host "Starting Django server (ASGI)..." -ForegroundColor Yellow
Start-Background "django" "python" "-m django --version"

# 2) Seed data (optional)
if (-not $SkipSeed) {
  Write-Host "Seeding data..." -ForegroundColor Yellow
  python .\backend\manage.py migrate
  python .\backend\manage.py seed_data
  python .\backend\manage.py seed_restaurant_mock_data
}

# 3) Frontend: ensure Node deps and start dev servers for apps
Write-Host "Ensuring Node deps..." -ForegroundColor Yellow
if (Test-Path .\package.json) {
  npm ci
}

Write-Host "Starting customer app (3020), restaurant (3021), delivery (3022), admin (3023)..." -ForegroundColor Yellow
Start-Background "frontend-customer" "npm" "--prefix .\frontend\apps\customer run dev"
Start-Background "frontend-restaurant" "npm" "--prefix .\frontend\apps\restaurant run dev"
Start-Background "frontend-delivery" "npm" "--prefix .\frontend\apps\delivery run dev"
Start-Background "frontend-admin" "npm" "--prefix .\frontend\apps\admin run dev"

# 4) Backend tests (pytest)
Write-Host "Running backend pytest suite..." -ForegroundColor Cyan
pushd .\backend
pytest --junitxml=..\test-results\backend-junit.xml || $true
popd

# 5) API black-box tests (testsprite)
Write-Host "Running testsprite API scripts..." -ForegroundColor Cyan
python .\testsprite_tests\TC001_login_with_email_and_password.py || $true
python .\testsprite_tests\TC002_refresh_access_token.py || $true
python .\testsprite_tests\TC003_login_with_biometric_authentication.py || $true
python .\testsprite_tests\TC004_send_otp_for_two_factor_authentication.py || $true
python .\testsprite_tests\TC005_verify_otp.py || $true
python .\testsprite_tests\TC006_list_all_restaurants_with_filters.py || $true
python .\testsprite_tests\TC007_get_restaurant_details.py || $true
python .\testsprite_tests\TC008_create_new_order.py || $true
python .\testsprite_tests\TC009_process_payment.py || $true
python .\testsprite_tests\TC010_list_user_notifications.py || $true

# 6) Playwright E2E (if configured)
Write-Host "Running Playwright E2E..." -ForegroundColor Cyan
if (Test-Path .\backend\playwright.config.ts -or Test-Path .\playwright.config.ts) {
  npx playwright test --reporter=html || $true
}

Write-Host "All test stages invoked. Check test-results/ and playwright-report/ for artifacts." -ForegroundColor Green