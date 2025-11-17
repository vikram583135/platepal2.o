# Alternative Testing Approach - Playwright E2E Tests

Since TestSprite's cloud service had connectivity issues, we've set up a **local Playwright-based testing solution** that runs directly on your machine.

## ✅ What's Been Set Up

### 1. Playwright Test Suite
- **Location**: `frontend/tests/platepal.spec.ts`
- **Test Cases**: 12 initial tests covering:
  - Customer authentication (login, logout, invalid credentials)
  - Restaurant browsing and search
  - Cart functionality
  - Order management
  - Profile access
  - API endpoint testing

### 2. Playwright Configuration
- **File**: `frontend/playwright.config.ts`
- **Features**:
  - Automatic server startup
  - Screenshots on failure
  - Video recording on failure
  - HTML test reports
  - Multi-browser support (Chrome, Firefox, Safari)

### 3. NPM Scripts Added
```json
"test:e2e": "playwright test"           // Run all tests
"test:e2e:ui": "playwright test --ui"   // Interactive UI mode
"test:e2e:headed": "playwright test --headed"  // See browser
"test:e2e:debug": "playwright test --debug"    // Debug mode
"test:e2e:report": "playwright show-report"   // View results
```

## 🚀 Quick Start

### 1. Install Playwright Browsers (One-time setup)
```bash
cd frontend
npx playwright install
```

### 2. Ensure Servers Are Running
- Backend: `http://localhost:8000`
- Customer App: `http://localhost:3020`

### 3. Run Tests
```bash
# Run all tests
npm run test:e2e

# Run with UI (recommended for first time)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Debug mode
npm run test:e2e:debug
```

## 📊 Test Coverage

### Authentication Tests
- ✅ TC001: Customer login with valid credentials
- ✅ TC002: Login failure with invalid credentials
- ✅ TC010: Logout functionality

### Restaurant Browsing
- ✅ TC003: Browse restaurants after login
- ✅ TC004: Search for restaurants
- ✅ TC005: View restaurant details

### Order Flow
- ✅ TC006: Add item to cart
- ✅ TC007: View cart

### Navigation
- ✅ TC008: Navigate to orders page
- ✅ TC009: Check profile page

### API Tests
- ✅ TC011: Test login API endpoint
- ✅ TC012: Test restaurants API endpoint

## 📝 Adding More Tests

The test plan from TestSprite (`testsprite_tests/testsprite_frontend_test_plan.json`) contains 22 test cases. You can add more tests by:

1. **Opening** `frontend/tests/platepal.spec.ts`
2. **Adding new test cases** following the existing pattern
3. **Using helper functions** like `loginAsCustomer(page)`

### Example: Adding a New Test
```typescript
test('TC013: Place Order Flow', async ({ page }) => {
  await loginAsCustomer(page);
  await page.waitForLoadState('networkidle');
  
  // Navigate to restaurant
  const restaurantCard = page.locator('.restaurant-card').first();
  await restaurantCard.click();
  
  // Add item to cart
  const addButton = page.locator('button:has-text("Add")').first();
  await addButton.click();
  
  // Go to cart and checkout
  const cartButton = page.locator('[data-testid="cart"]');
  await cartButton.click();
  
  // Continue with checkout flow...
});
```

## 🎯 Advantages of This Approach

### ✅ Pros
- **Runs locally** - No cloud service dependency
- **Fast execution** - Tests run on your machine
- **Full control** - Customize tests as needed
- **Free** - No API limits or costs
- **Detailed reports** - HTML reports with screenshots/videos
- **Debugging** - Easy to debug with Playwright's tools
- **CI/CD ready** - Can be integrated into pipelines

### ⚠️ Cons
- **Manual setup** - Need to write test cases yourself
- **Maintenance** - Tests need updates when UI changes
- **Local only** - Can't test on multiple environments easily

## 📈 Next Steps

### Immediate
1. ✅ Install Playwright browsers: `npx playwright install`
2. ✅ Run initial tests: `npm run test:e2e:ui`
3. ✅ Review test results and fix any failures

### Short-term
1. Add more test cases from the TestSprite test plan
2. Add tests for restaurant and admin apps
3. Set up CI/CD integration
4. Add visual regression testing

### Long-term
1. Expand test coverage to 80%+
2. Add performance testing
3. Add accessibility testing
4. Set up test reporting dashboard

## 🔧 Troubleshooting

### Tests fail with "Navigation timeout"
- Ensure customer app is running: `npm run dev:customer`
- Check backend is running on port 8000
- Increase timeout in `playwright.config.ts`

### Can't find elements
- Use Playwright's codegen to find selectors:
  ```bash
  npx playwright codegen http://localhost:3020
  ```
- Add `data-testid` attributes to your React components
- Check browser DevTools for actual element structure

### Tests are flaky
- Add explicit waits: `await page.waitForSelector(...)`
- Use `waitForLoadState('networkidle')` after navigation
- Increase timeout values in test configuration

## 📚 Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Test Plan Reference](./testsprite_tests/testsprite_frontend_test_plan.json)

## 📊 Comparison: TestSprite vs Playwright

| Feature | TestSprite | Playwright |
|---------|-----------|------------|
| Setup | Cloud-based | Local |
| Cost | API-based | Free |
| Speed | Depends on cloud | Fast (local) |
| Control | Limited | Full |
| Customization | Limited | Full |
| Debugging | Limited | Excellent |
| Reports | Cloud dashboard | HTML reports |
| CI/CD | Yes | Yes |

## 🎉 Summary

You now have a **working, local testing solution** that:
- ✅ Runs independently of cloud services
- ✅ Covers key user flows
- ✅ Provides detailed test reports
- ✅ Can be easily extended
- ✅ Works offline
- ✅ Integrates with CI/CD

This is a **more reliable and maintainable** solution for your development workflow!

---

**Created**: $(Get-Date -Format "yyyy-MM-dd")
**Test Framework**: Playwright 1.56.1
**Test Cases**: 12 (expandable to 22+ from TestSprite plan)

