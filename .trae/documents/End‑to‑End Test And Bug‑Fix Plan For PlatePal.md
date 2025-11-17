## Scope And Goals
- Cover backend APIs, websockets, and all four frontend apps (`customer`, `restaurant`, `delivery`, `admin`) with automated scripts.
- Produce reproducible test runs, artifacts (HTML reports, traces, videos), and clear pass/fail signals.
- Identify and fix critical logic, security, and reliability bugs discovered during research.

## Test Stack
- Backend unit/integration: `pytest` + `pytest-django` using DRF `APIClient` (configured in `backend/pytest.ini`).
- API black-box: Python `requests` scripts (existing `testsprite_tests/*.py`).
- Frontend E2E: Playwright with traces/video; run against dev servers for each app.
- WebSocket: Django Channels tests using `pytest-asyncio` for consumer auth and event replay.
- Performance smoke: k6 optional smoke scripts for hot paths (auth, list restaurants, place order).

## Environment Setup
- Services: PostgreSQL, Redis, Django (`runserver`), Channels (ASGI), and Vite dev servers for each app.
- Seed data: Run management commands for base users and restaurants (`backend/apps/accounts/management/commands/seed_data.py`, `backend/apps/restaurants/management/commands/seed_restaurant_mock_data.py`).
- Config alignment: Ensure `testsprite-config.json` URLs match real endpoints and ports.

## Orchestration Scripts
- Windows PowerShell entrypoint `run-all-tests.ps1` (to be added):
  - Start Redis and Postgres if not running.
  - Start Django ASGI and all four Vite servers in background.
  - Run seed commands.
  - Execute backend `pytest` suite; save JUnit/coverage.
  - Execute `testsprite_tests` API scripts; save JSON summaries.
  - Execute Playwright suites per app; save HTML reports and traces.
- Node helper scripts:
  - `scripts/debug-login.cjs` already present; add small wrappers for e2e flows if needed.

## Backend Coverage (APIs)
- Accounts: email/password login, token refresh, registration, 2FA OTP, biometric register/login, devices, sessions, cookie consent.
- Restaurants: list, detail, menu search/filters, promotions.
- Orders: create, update, status transitions, customer view, restaurant actions.
- Deliveries: offers, accept/expire, rider shifts, wallet, offline actions, trip logs. See tests already in `backend/apps/deliveries/tests/test_views.py:58,64,75,89,118,128,189,204,238,245,264,278,342`.
- Payments: create intent/confirm, capture, refunds, wallet add/history. References: `backend/apps/payments/views.py:236` (create intent), `backend/apps/payments/views.py:270` (confirm), `backend/apps/payments/views.py:61` (capture), `backend/apps/payments/views.py:391` (wallet).
- Notifications/Support/Subscriptions/Rewards/Analytics/Inventory/Admin Panel basic endpoints.
- Docs: Swagger/Redoc reachable (`backend/platepal/urls.py:41,42`).

## WebSocket Tests
- Auth handshake: token via query/header in consumers; verify accepting only valid JWT (`backend/websockets/consumers.py:39–64`).
- Group join/leave per role: restaurant, delivery, customer, admin consumer groups (`backend/websockets/consumers.py:154,241,319,411`).
- Event replay via `since_event_id` (`backend/websockets/consumers.py:88–151`).
- Broadcast smoke via `apps.events.broadcast.*` to verify delivery to correct groups.

## Frontend E2E Coverage
- Customer: login, browse/search restaurants, add to cart, checkout, payment intent+confirm, order tracking socket.
- Restaurant: login, dashboard, accept/reject orders, inventory updates.
- Delivery: login, start/stop shift, view offers, accept job, wallet balance/history.
- Admin: login, manage users/roles, view analytics, incidents and alerts.
- Use Playwright to navigate pages and validate React state/store changes, API calls, and UI outcomes. Save traces/videos to `playwright-report/` and `test-results/` (existing folders present).

## API Black‑Box Tests (testsprite)
- Finish and run `testsprite_tests/TC001..TC010` against configured hosts; export aggregated JSON to `testsprite_tests/tmp/test_results.json`.
- Update endpoints in `testsprite-config.json` that mismatch real routes (see Issues below).

## Reporting And Artifacts
- Backend: `pytest --junitxml=backend-test-results.xml`; optional `pytest-cov` for coverage.
- Playwright: `--reporter=html` with `trace:on-first-retry`.
- testsprite: write structured JSON with per-case status and latencies.

## Issues Found (To Fix)
- CORS dev origins always included even in production: `backend/platepal/settings.py:179–201`. Fix by adding dev origins only when `DEBUG` is true.
- Payment intent ownership check inconsistent:
  - Uses `Order.objects.get(id=order_id, user=request.user)` in `backend/apps/payments/views.py:248` but everywhere else uses `customer`; should be `customer`. Also verify ownership consistently in serializers.
- Payment creation missing authorization on order: `backend/apps/payments/serializers.py:35` fetches order without checking it belongs to `request.user`. Add ownership validation and error handling.
- BotDetection header check incorrect: checks `'Authorization'` instead of `'HTTP_AUTHORIZATION'` and may block legit API tokens (`backend/apps/accounts/middleware.py:106–111`). Use `'HTTP_AUTHORIZATION'`.
- Biometric register missing `timedelta` import: `backend/apps/accounts/views.py:631` uses `timedelta` without importing it at function/module scope; add import to avoid `NameError`.
- testsprite config endpoints mismatch real ones: `testsprite-config.json:112–127` refer to `/api/accounts/...` while real auth routes are under `/api/auth/...` (`backend/platepal/urls.py:27` and `backend/apps/accounts/urls.py:25–33`).

## Fix Plan
- Settings: gate `DEFAULT_CORS_ALLOWED_ORIGINS` behind `DEBUG` or a dedicated `ENABLE_DEV_CORS` flag.
- Payments:
  - Replace `Order.objects.get(id=..., user=...)` with `customer=...` and unify across views/serializers.
  - In `PaymentCreateSerializer.create`, assert `order.customer == request.user`; raise `ValidationError` otherwise.
- Middleware: change header lookup to `request.META.get('HTTP_AUTHORIZATION')`.
- Accounts biometric: add `from datetime import timedelta` at module top or inside `register`.
- testsprite config: correct routes and base URLs; align ports to `backend/platepal/settings.py:180–195` dev origins.

## Efficiency Tactics
- Reuse seeded data across suites via `--reuse-db`; parallelize Playwright across apps; cache npm/pip deps.
- Use idempotency header in state‑changing API tests to reduce flakes (`backend/apps/accounts/middleware.py:120–206`).
- Record traces only on retry to keep runs fast.

## Execution Sequence
1) Bootstrap services and seed data.
2) Run backend `pytest` (unit/integration).
3) Run testsprite API scripts; export summary.
4) Run Playwright suites for each app; export HTML report.
5) Run websocket consumer tests.
6) Apply fixes listed; rerun affected suites to verify.
7) Deliver consolidated report and a short list of remaining gaps.

## Deliverables
- Scripts to start services and run all tests, plus CI‑ready commands.
- Test reports (JUnit, HTML), Playwright traces/videos, API JSON summaries.
- Patch set implementing the fixes above with references.

## Next Step
- Confirm this plan; I will then add the orchestration scripts, implement the fixes, and run the full test pass to produce artifacts.