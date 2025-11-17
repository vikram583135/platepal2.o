# PlatePal E2E Tests with Playwright

This directory contains end-to-end tests for the PlatePal application using Playwright.

## Setup

1. **Install Playwright browsers** (if not already installed):
   ```bash
   cd frontend
   npx playwright install
   ```

2. **Ensure servers are running**:
   - Backend: `http://localhost:8000`
   - Customer App: `http://localhost:3020`

## Running Tests

### Run all tests
```bash
cd frontend
npx playwright test
```

### Run specific test file
```bash
npx playwright test platepal.spec.ts
```

### Run tests in UI mode (interactive)
```bash
npx playwright test --ui
```

### Run tests in headed mode (see browser)
```bash
npx playwright test --headed
```

### Run tests for specific browser
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### Run tests in debug mode
```bash
npx playwright test --debug
```

## Test Structure

Tests are organized based on the TestSprite-generated test plan:

- **Authentication Tests**: Login, logout, invalid credentials
- **Restaurant Browsing**: Search, view details, filters
- **Order Flow**: Add to cart, checkout, order placement
- **User Profile**: Profile management, settings
- **API Tests**: Backend API endpoint testing

## Test Accounts

The tests use these predefined accounts:
- Customer: `customer@platepal.com` / `customer123`
- Restaurant: `restaurant@platepal.com` / `restaurant123`
- Admin: `admin@platepal.com` / `admin123`

## Viewing Test Results

After running tests, view the HTML report:
```bash
npx playwright show-report
```

## Configuration

Test configuration is in `playwright.config.ts`. Key settings:
- Base URL: `http://localhost:3020`
- Timeout: 60 seconds per test
- Retries: 0 (local), 2 (CI)
- Screenshots: On failure
- Videos: On failure

## Adding New Tests

1. Add test cases to `platepal.spec.ts`
2. Follow the existing test structure
3. Use helper functions like `loginAsCustomer()` for common actions
4. Run tests to verify they work

## Troubleshooting

### Tests fail with "Navigation timeout"
- Ensure the customer app is running on port 3020
- Check that the backend API is running on port 8000

### Tests can't find elements
- Use browser DevTools to inspect the page
- Check if selectors need to be updated
- Consider using `data-testid` attributes in your components

### Tests are flaky
- Increase timeout values
- Add explicit waits for network requests
- Use `waitForLoadState('networkidle')` when needed

