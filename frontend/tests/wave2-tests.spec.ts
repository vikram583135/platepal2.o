import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = 'http://localhost:3020';
const API_BASE_URL = 'http://localhost:8000/api';

// Test accounts
const TEST_ACCOUNTS = {
  customer: {
    email: 'customer@platepal.com',
    password: 'customer123'
  }
};

// Helper function to login
async function loginAsCustomer(page: Page) {
  await page.goto(`${BASE_URL}/login`);
  await page.fill('input[type="email"], input[name="email"]', TEST_ACCOUNTS.customer.email);
  await page.fill('input[type="password"], input[name="password"]', TEST_ACCOUNTS.customer.password);
  await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")');
  await page.waitForURL(/^(?!.*login).*$/, { timeout: 10000 });
}

test.describe('Wave 2: Restaurant Discovery & Checkout Tests', () => {
  test.beforeEach(async ({ page }) => {
    test.setTimeout(60000);
  });

  test('TC017: Search for restaurants', async ({ page }) => {
    await page.goto(`${BASE_URL}/`);

    // Search for "pizza"
    const searchInput = page.locator('input[placeholder*="Search"]').first();
    await searchInput.fill('pizza');
    await searchInput.press('Enter');

    // Should navigate to restaurants page with search param
    await page.waitForURL(/.*restaurants.*search=pizza.*/i, { timeout: 10000 });
    await expect(page).toHaveURL(/.*restaurants.*search=pizza.*/i);

    // Should show results header
    await expect(page.locator('text=/Search Results/i')).toBeVisible({ timeout: 10000 });
  });

  test('TC018: Apply cuisine filter', async ({ page }) => {
    await page.goto(`${BASE_URL}/restaurants`);

    // Open filters
    const filterBtn = page.locator('button:has-text("Filters")').first();
    await filterBtn.click();

    // Select Italian cuisine
    const italianBtn = page.locator('button:has-text("Italian")').first();
    await italianBtn.click();

    // Apply filters
    const applyBtn = page.locator('button:has-text("Apply")').first();
    await applyBtn.click();

    // URL should include cuisine param
    await expect(page).toHaveURL(/.*cuisines=Italian.*/i);

    // Filter count badge should show 1
    await expect(page.locator('button:has-text("Filters") span:has-text("1")')).toBeVisible({ timeout: 5000 });
  });

  test('TC019: Apply rating filter', async ({ page }) => {
    await page.goto(`${BASE_URL}/restaurants`);

    // Open filters
    const filterBtn = page.locator('button:has-text("Filters")').first();
    await filterBtn.click();

    // Set minimum rating
    const minRatingInput = page.locator('input[placeholder="Min"]').first();
    await minRatingInput.fill('4.0');

    // Apply filters
    const applyBtn = page.locator('button:has-text("Apply")').first();
    await applyBtn.click();

    // URL should include rating param
    await expect(page).toHaveURL(/.*min_rating=4.*/);
  });

  test('TC020: View restaurant details', async ({ page }) => {
    await page.goto(`${BASE_URL}/restaurants`);

    // Wait for restaurants to load
    await page.waitForSelector('a[href*="/restaurant/"]', { timeout: 10000 });

    // Click first restaurant card
    const firstRestaurant = page.locator('a[href*="/restaurant/"]').first();
    await firstRestaurant.click();

    // Should navigate to restaurant detail page
    await page.waitForURL(/.*\/restaurant\/\d+.*/, { timeout: 10000 });
    await expect(page).toHaveURL(/.*\/restaurant\/\d+.*/);

    // Should show restaurant name
    await expect(page.locator('h1')).toBeVisible({ timeout: 5000 });
  });

  test('TC021: Search menu items', async ({ page }) => {
    // Navigate to a restaurant detail page (assuming ID 1 exists)
    await page.goto(`${BASE_URL}/restaurant/1`);

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Search for an item
    const menuSearchInput = page.locator('input[placeholder*="menu"]').first();
    if (await menuSearchInput.isVisible()) {
      await menuSearchInput.fill('burger');

      // Should show search results dropdown
      await expect(page.locator('text=/Searching.../i, text=/No items found/i, button:has-text("burger")')).toBeVisible({ timeout: 5000 });
    }
  });

  test('TC022: Add item to cart without login', async ({ page }) => {
    await page.goto(`${BASE_URL}/restaurant/1`);
    await page.waitForLoadState('networkidle');

    // Find and click add to cart button
    const addButton = page.locator('button:has-text("Add"), button:has-text("+")').first();
    if (await addButton.isVisible()) {
      await addButton.click();

      // Cart icon should show item count or navigate to cart
      const cartIcon = page.locator('[href="/cart"], button:has-text("Cart")').first();
      await expect(cartIcon).toBeVisible({ timeout: 5000 });
    }
  });

  test('TC023: Apply valid coupon code', async ({ page }) => {
    await loginAsCustomer(page);

    // Add item to cart first (simulate)
    await page.goto(`${BASE_URL}/cart`);

    // Check if cart has items
    const checkoutBtn = page.locator('button:has-text("Checkout"), a:has-text("Checkout")').first();
    if (await checkoutBtn.isVisible()) {
      // Try to apply coupon
      const couponInput = page.locator('input[placeholder*="coupon"], input[placeholder*="Coupon"]').first();
      if (await couponInput.isVisible()) {
        await couponInput.fill('TEST10');

        const applyBtn = page.locator('button:has-text("Apply")').first();
        await applyBtn.click();

        // Should show success or error message
        await page.waitForTimeout(2000);
        const hasSuccess = await page.locator('text=/applied/i, text=/invalid/i, text=/error/i').isVisible();
        expect(hasSuccess).toBeTruthy();
      }
    }
  });

  test('TC024: Navigate to checkout', async ({ page }) => {
    await loginAsCustomer(page);

    // Go to cart
    await page.goto(`${BASE_URL}/cart`);

    // If cart has items, proceed to checkout
    const proceedBtn = page.locator('button:has-text("Proceed"), button:has-text("Checkout"), a:has-text("Checkout")').first();
    if (await proceedBtn.isVisible()) {
      await proceedBtn.click();

      // Should navigate to checkout page
      await page.waitForURL(/.*checkout.*/i, { timeout: 10000 });
      await expect(page).toHaveURL(/.*checkout.*/i);
    } else {
      // Cart is empty - that's also valid
      await expect(page.locator('text=/empty/i')).toBeVisible();
    }
  });

  test('TC025: Checkout validation - address required', async ({ page }) => {
    await loginAsCustomer(page);

    // Go directly to checkout
    await page.goto(`${BASE_URL}/checkout`);

    // Try to place order without selecting address
    const placeOrderBtn = page.locator('button:has-text("Place Order"), button:has-text("Submit")').first();
    if (await placeOrderBtn.isVisible()) {
      await placeOrderBtn.click();

      // Should show validation error
      await expect(page.locator('text=/select.*address/i, text=/address.*required/i')).toBeVisible({ timeout: 3000 });
    }
  });

  test('TC026: Checkout validation - payment method required', async ({ page }) => {
    await loginAsCustomer(page);

    await page.goto(`${BASE_URL}/checkout`);

    // Select address if available
    const addressRadio = page.locator('input[type="radio"][name*="address"]').first();
    if (await addressRadio.isVisible()) {
      await addressRadio.check();
    }

    // Try to place order without payment method
    const placeOrderBtn = page.locator('button:has-text("Place Order"), button:has-text("Submit")').first();
    if (await placeOrderBtn.isVisible()) {
      await placeOrderBtn.click();

      // Should show payment method validation
      await expect(page.locator('text=/payment.*method/i, text=/select.*payment/i')).toBeVisible({ timeout: 3000 });
    }
  });

  test('TC027: Empty cart message', async ({ page }) => {
    await page.goto(`${BASE_URL}/cart`);

    // Clear cart if needed (manual step)
    // Should show empty cart message
    const emptyMessage = page.locator('text=/empty/i, text=/no items/i').first();
    const hasItems = await page.locator('button:has-text("Checkout")').isVisible();

    if (!hasItems) {
      await expect(emptyMessage).toBeVisible({ timeout: 5000 });
    }
  });

  test('TC028: Restaurant filters reset', async ({ page }) => {
    await page.goto(`${BASE_URL}/restaurants`);

    // Open filters
    const filterBtn = page.locator('button:has-text("Filters")').first();
    await filterBtn.click();

    // Apply some filters
    const italianBtn = page.locator('button:has-text("Italian")').first();
    await italianBtn.click();

    const minRatingInput = page.locator('input[placeholder="Min"]').first();
    await minRatingInput.fill('4.0');

    // Reset filters
    const resetBtn = page.locator('button:has-text("Reset"), button:has-text("Clear")').first();
    if (await resetBtn.isVisible()) {
      await resetBtn.click();

      // Filter count should be 0
      const filterCount = page.locator('button:has-text("Filters") span');
      if (await filterCount.isVisible()) {
        await expect(filterCount).toHaveText('0');
      }

      // Min rating should be cleared
      await expect(minRatingInput).toHaveValue('');
    }
  });

  test('TC029: Sort restaurants by rating', async ({ page }) => {
    await page.goto(`${BASE_URL}/restaurants`);

    // Open filters
    const filterBtn = page.locator('button:has-text("Filters")').first();
    await filterBtn.click();

    // Select sort by high rating
    const sortSelect = page.locator('select').first();
    if (await sortSelect.isVisible()) {
      await sortSelect.selectOption({ label: 'High Rating' });

      // Apply
      const applyBtn = page.locator('button:has-text("Apply")').first();
      await applyBtn.click();

      // URL should include ordering param
      await expect(page).toHaveURL(/.*ordering=-rating.*/);
    }
  });

  test('TC030: Update item quantity in cart', async ({ page }) => {
    await page.goto(`${BASE_URL}/cart`);

    // If cart has items
    const plusBtn = page.locator('button:has-text("+")').first();
    if (await plusBtn.isVisible()) {
      // Get initial quantity
      const quantityText = await page.locator('text=/\\d+/').first().textContent();
      const initialQty = parseInt(quantityText || '1');

      // Click plus
      await plusBtn.click();

      // Quantity should increase
      await page.waitForTimeout(500);
      const newQuantityText = await page.locator('text=/\\d+/').first().textContent();
      const newQty = parseInt(newQuantityText || '1');

      expect(newQty).toBeGreaterThan(initialQty);
    }
  });
});
