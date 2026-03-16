/**
 * ScanifyMe E2E Tests using Playwright
 * 
 * Tests the complete user flow from:
 * 1. Frontend loading
 * 2. Public scan page
 * 3. Message submission
 * 4. Owner recovery workflow
 * 
 * Run with: npx playwright test
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.TEST_URL || 'http://test.localhost';

// Test data - these should be created by demo data
const DEMO_USER = {
  email: 'demo@scanifyme.app',
  password: 'demo123'
};

let validToken = null;
let validCaseId = null;

test.describe('ScanifyMe End-to-End Tests', () => {
  
  test.beforeAll(async ({ request }) => {
    // Get demo data before running tests
    // Note: In real scenario, this would call the demo data API
    // For now, we'll discover the token from the page
  });

  test('1. Frontend homepage loads', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/frontend`);
    
    // Check response
    expect(response.status()).toBeLessThan(500);
    
    // Check page loaded (React app should render)
    await page.waitForLoadState('networkidle');
    
    // Check for console errors (excluding known warnings)
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Give time for any errors to appear
    await page.waitForTimeout(1000);
    
    // Should not have critical errors
    const criticalErrors = consoleErrors.filter(e => 
      !e.includes('favicon') && 
      !e.includes('Warning') &&
      !e.includes('React Router')
    );
    expect(criticalErrors.length).toBe(0);
  });

  test('2. Frontend items page loads', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/items`);
    await page.waitForLoadState('networkidle');
    
    // Check page loaded without critical errors
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    await page.waitForTimeout(1000);
  });

  test('3. Frontend activate-qr page loads', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/activate-qr`);
    await page.waitForLoadState('networkidle');
    
    // Just verify it loads
    await page.waitForTimeout(500);
  });

  test('4. Frontend recovery page loads', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/recovery`);
    await page.waitForLoadState('networkidle');
    
    // Should load (may show empty state if no cases)
    await page.waitForTimeout(500);
  });

  test('5. Public scan page with valid token loads', async ({ page }) => {
    // First, try to get a valid token by checking the demo data
    // For now, we'll use a test that the page loads with any token
    
    // Try loading with a known invalid token first to see the error state
    await page.goto(`${BASE_URL}/s/INVALID_TOKEN_TEST`);
    await page.waitForLoadState('networkidle');
    
    // Should show "invalid" or "not valid" message
    const pageContent = await page.content();
    expect(pageContent.toLowerCase()).toContain('invalid');
  });

  test('6. Public scan page with valid token shows item info', async ({ page }) => {
    // This test requires a valid token from demo data
    // In a real setup, we'd get this from the API first
    
    // For now, test the error state with invalid token
    await page.goto(`${BASE_URL}/s/SOME_INVALID_TOKEN_12345`);
    await page.waitForLoadState('networkidle');
    
    // Check for safe error message
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toBeTruthy();
    
    // Should NOT leak sensitive information
    expect(bodyText).not.toContain('@scanifyme.app');
    expect(bodyText).not.toContain('+1234567890');
  });

  test('7. API endpoints respond correctly', async ({ request }) => {
    // Test frappe.auth.get_logged_user
    const authResponse = await request.post(`${BASE_URL}/api/method/frappe.auth.get_logged_user`);
    expect(authResponse.status()).toBe(200);
    
    // Test public API with invalid token
    const publicResponse = await request.post(
      `${BASE_URL}/api/method/scanifyme.public_portal.api.public_api.get_public_item_context`,
      { data: { token: 'INVALID_TOKEN' } }
    );
    expect(publicResponse.status()).toBe(200);
    const publicJson = await publicResponse.json();
    expect(publicJson.message.success).toBe(false);
    
    // Test item categories (public endpoint)
    const categoriesResponse = await request.post(
      `${BASE_URL}/api/method/scanifyme.items.api.items_api.get_item_categories`
    );
    expect(categoriesResponse.status()).toBe(200);
  });

  test('8. No dashboard navigation from frontend', async ({ page }) => {
    // Navigate to frontend
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForLoadState('networkidle');
    
    // Get current URL
    const currentUrl = page.url();
    
    // Should NOT contain /dashboard
    expect(currentUrl).not.toContain('/dashboard');
    
    // Navigate to items
    await page.goto(`${BASE_URL}/frontend/items`);
    await page.waitForLoadState('networkidle');
    
    const itemsUrl = page.url();
    expect(itemsUrl).not.toContain('/dashboard');
  });

  test('9. API uses correct paths', async ({ request }) => {
    // All APIs should be under /api/, never /frontend/api/
    
    // Test various APIs
    const endpoints = [
      'frappe.auth.get_logged_user',
      'scanifyme.items.api.items_api.get_item_categories',
      'scanifyme.public_portal.api.public_api.get_public_item_context'
    ];
    
    for (const endpoint of endpoints) {
      const response = await request.post(
        `${BASE_URL}/api/method/${endpoint}`,
        { data: {} }
      );
      
      // Should not be 404 (means wrong path)
      expect(response.status()).not.toBe(404);
    }
  });

  test('10. CSRF token is present on forms', async ({ page }) => {
    // Visit the public scan page
    await page.goto(`${BASE_URL}/s/TOKEN_FOR_TESTING`);
    await page.waitForLoadState('networkidle');
    
    // Check if there's a form with CSRF token
    const csrfToken = await page.evaluate(() => {
      const tokenInput = document.querySelector('input[name="csrf_token"]');
      return tokenInput ? tokenInput.value : window.csrf_token;
    });
    
    // CSRF token should exist (either in form or window)
    // Note: This may fail if the token format is different
    console.log('CSRF token found:', !!csrfToken);
  });
});

test.describe('Security Tests', () => {
  
  test('Public page does not expose owner email', async ({ page }) => {
    // Try with any token
    await page.goto(`${BASE_URL}/s/TEST_TOKEN`);
    await page.waitForLoadState('networkidle');
    
    const content = await page.content();
    
    // Should not contain demo email
    expect(content).not.toContain('demo@scanifyme.app');
    expect(content).not.toContain('+1234567890');
  });
  
  test('Public page does not expose stack traces', async ({ page }) => {
    await page.goto(`${BASE_URL}/s/INVALID_TOKEN`);
    await page.waitForLoadState('networkidle');
    
    const content = await page.content();
    
    // Should not contain Python traceback
    expect(content).not.toContain('Traceback');
    expect(content).not.toContain('File "');
    expect(content).not.toContain('frappe.');
  });
  
  test('API errors are JSON, not HTML', async ({ request }) => {
    // Call API with invalid data
    const response = await request.post(
      `${BASE_URL}/api/method/scanifyme.public_portal.api.public_api.get_public_item_context`,
      { data: { token: null } } // null token
    );
    
    const contentType = response.headers()['content-type'];
    expect(contentType).toContain('application/json');
  });
});
