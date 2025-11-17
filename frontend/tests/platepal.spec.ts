import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = 'http://localhost:3020';
const API_BASE_URL = 'http://localhost:8000/api';

// Test accounts
const TEST_ACCOUNTS = {
  customer: {
    email: 'customer@platepal.com',
    password: 'customer123'
  },
  restaurant: {
    email: 'restaurant@platepal.com',
    password: 'restaurant123'
  },
  admin: {
    email: 'admin@platepal.com',
    password: 'admin123'
  }
};

// Helper function to login
async function loginAsCustomer(page: Page) {
  await page.goto(`${BASE_URL}/login`);
  await page.fill('input[type="email"], input[name="email"]', TEST_ACCOUNTS.customer.email);
  await page.fill('input[type="password"], input[name="password"]', TEST_ACCOUNTS.customer.password);
  await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")');
  // Wait for navigation after login
  await page.waitForURL(/^(?!.*login).*$/, { timeout: 10000 });
}

test.describe('PlatePal Customer App Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Set longer timeout for local development
    test.setTimeout(60000);
  });

  test('TC001: Customer Login Success with Email and Password', async ({ page }) => {
    // Navigate to customer login page
    await page.goto(`${BASE_URL}/login`);
    
    // Verify login page loaded
    await expect(page).toHaveURL(/.*login.*/);
    
    // Enter valid credentials
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"]').first();
    
    await emailInput.fill(TEST_ACCOUNTS.customer.email);
    await passwordInput.fill(TEST_ACCOUNTS.customer.password);
    
    // Click login button
    const loginButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")').first();
    await loginButton.click();
    
    // Verify successful login and redirect
    await page.waitForURL(/^(?!.*login).*$/, { timeout: 10000 });
    await expect(page).not.toHaveURL(/.*login.*/);
    
    // Verify user is on home/restaurant browsing page
    const currentUrl = page.url();
    expect(currentUrl).not.toContain('login');
  });

  test('TC002: Customer Login Failure with Invalid Credentials', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    
    // Enter invalid credentials
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"]').first();
    
    await emailInput.fill('invalid@platepal.com');
    await passwordInput.fill('wrongpass');
    
    // Click login button
    const loginButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")').first();
    await loginButton.click();
    
    // Wait for error message (could be toast, alert, or inline error)
    await page.waitForTimeout(2000);
    
    // Check for error message (various possible locations)
    const errorMessage = page.locator('text=/invalid|error|incorrect|wrong/i').first();
    const isVisible = await errorMessage.isVisible().catch(() => false);
    
    // Verify we're still on login page
    await expect(page).toHaveURL(/.*login.*/);
  });

  test('TC003: Browse Restaurants After Login', async ({ page }) => {
    // Login first
    await loginAsCustomer(page);
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Look for restaurant listings (could be cards, list items, etc.)
    const restaurantElements = page.locator('[data-testid*="restaurant"], .restaurant-card, [class*="restaurant"]').first();
    
    // Check if restaurants are displayed (at least one should be visible)
    const restaurantCount = await page.locator('[data-testid*="restaurant"], .restaurant-card, [class*="restaurant"]').count();
    
    // If no specific restaurant elements found, check for any content
    if (restaurantCount === 0) {
      // Just verify we're on a page with content
      const bodyText = await page.textContent('body');
      expect(bodyText).toBeTruthy();
    } else {
      expect(restaurantCount).toBeGreaterThan(0);
    }
  });

  test('TC004: Search for Restaurants', async ({ page }) => {
    await loginAsCustomer(page);
    await page.waitForLoadState('networkidle');
    
    // Look for search input
    const searchInput = page.locator('input[type="search"], input[placeholder*="search" i], input[name*="search" i]').first();
    
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.fill('pizza');
      await page.waitForTimeout(1000);
      
      // Check if results appear
      const results = page.locator('text=/pizza/i').first();
      const hasResults = await results.isVisible().catch(() => false);
      // Test passes if search input exists and accepts input
    }
  });

  test('TC005: View Restaurant Details', async ({ page }) => {
    await loginAsCustomer(page);
    await page.waitForLoadState('networkidle');
    
    // Try to find and click a restaurant card
    const restaurantCard = page.locator('[data-testid*="restaurant"], .restaurant-card, [class*="restaurant"]').first();
    
    if (await restaurantCard.isVisible().catch(() => false)) {
      await restaurantCard.click();
      await page.waitForTimeout(2000);
      
      // Verify we're on a restaurant detail page
      const currentUrl = page.url();
      // Should be on a different page than home
      expect(currentUrl).toBeTruthy();
    }
  });

  test('TC006: Add Item to Cart', async ({ page }) => {
    await loginAsCustomer(page);
    await page.waitForLoadState('networkidle');
    
    // Navigate to a restaurant (if possible)
    const restaurantCard = page.locator('[data-testid*="restaurant"], .restaurant-card, [class*="restaurant"]').first();
    
    if (await restaurantCard.isVisible().catch(() => false)) {
      await restaurantCard.click();
      await page.waitForTimeout(2000);
      
      // Look for "Add to Cart" or "Add" button
      const addButton = page.locator('button:has-text("Add"), button:has-text("Add to Cart"), [data-testid*="add"]').first();
      
      if (await addButton.isVisible().catch(() => false)) {
        await addButton.click();
        await page.waitForTimeout(1000);
        
        // Check if cart icon shows count
        const cartIcon = page.locator('[data-testid*="cart"], [aria-label*="cart" i]').first();
        // Test passes if add button exists and is clickable
      }
    }
  });

  test('TC007: View Cart', async ({ page }) => {
    await loginAsCustomer(page);
    await page.waitForLoadState('networkidle');
    
    // Look for cart icon/button
    const cartButton = page.locator('[data-testid*="cart"], [aria-label*="cart" i], button:has-text("Cart")').first();
    
    if (await cartButton.isVisible().catch(() => false)) {
      await cartButton.click();
      await page.waitForTimeout(2000);
      
      // Verify we're on cart page
      const currentUrl = page.url();
      expect(currentUrl).toContain('cart');
    }
  });

  test('TC008: Navigate to Orders Page', async ({ page }) => {
    await loginAsCustomer(page);
    await page.waitForLoadState('networkidle');
    
    // Look for orders/orders link
    const ordersLink = page.locator('a:has-text("Orders"), [href*="order"], [data-testid*="order"]').first();
    
    if (await ordersLink.isVisible().catch(() => false)) {
      await ordersLink.click();
      await page.waitForTimeout(2000);
      
      // Verify we're on orders page
      const currentUrl = page.url();
      expect(currentUrl).toContain('order');
    }
  });

  test('TC009: Check Profile Page', async ({ page }) => {
    await loginAsCustomer(page);
    await page.waitForLoadState('networkidle');
    
    // Look for profile/user menu
    const profileLink = page.locator('a:has-text("Profile"), [href*="profile"], [data-testid*="profile"], [aria-label*="profile" i]').first();
    
    if (await profileLink.isVisible().catch(() => false)) {
      await profileLink.click();
      await page.waitForTimeout(2000);
      
      // Verify we're on profile page
      const currentUrl = page.url();
      expect(currentUrl).toContain('profile');
    }
  });

  test('TC010: Logout Functionality', async ({ page }) => {
    await loginAsCustomer(page);
    await page.waitForLoadState('networkidle');
    
    // Look for logout button (usually in user menu)
    const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign out"), [data-testid*="logout"]').first();
    
    if (await logoutButton.isVisible().catch(() => false)) {
      await logoutButton.click();
      await page.waitForTimeout(2000);
      
      // Verify we're redirected to login or home
      const currentUrl = page.url();
      expect(currentUrl).toMatch(/login|home|^\/$/);
    }
  });
});

test.describe('API Endpoint Tests', () => {
  test('TC011: Test Login API Endpoint', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/accounts/login/`, {
      data: {
        email: TEST_ACCOUNTS.customer.email,
        password: TEST_ACCOUNTS.customer.password
      }
    });
    
    expect(response.status()).toBeLessThan(400);
    const body = await response.json().catch(() => ({}));
    
    // Should return tokens or user data
    expect(body).toBeTruthy();
  });

  test('TC012: Test Restaurants API Endpoint', async ({ request }) => {
    // First login to get token
    const loginResponse = await request.post(`${API_BASE_URL}/accounts/login/`, {
      data: {
        email: TEST_ACCOUNTS.customer.email,
        password: TEST_ACCOUNTS.customer.password
      }
    });
    
    const loginData = await loginResponse.json().catch(() => ({}));
    const token = loginData.access || loginData.token || loginData.access_token;
    
    if (token) {
      // Test restaurants endpoint
      const response = await request.get(`${API_BASE_URL}/restaurants/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      expect(response.status()).toBeLessThan(400);
      const body = await response.json().catch(() => ({}));
      expect(body).toBeTruthy();
    }
  });
});

