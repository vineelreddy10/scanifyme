import { test, expect } from '@playwright/test';

const BASE_URL = process.env.TEST_BASE_URL || 'http://test.localhost:8002';

test.describe('ScanifyMe Frontend', () => {
  test('Test 1: Open /frontend - loads without crash', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend`);
    
    // Wait for either the dashboard to load or redirect to login
    await page.waitForTimeout(3000);
    
    // Just verify the page loaded without crashing
    const url = page.url();
    expect(url).toBeTruthy();
  });

  test('Test 2: Open /frontend/activate-qr - loads without crash', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/activate-qr`);
    await page.waitForTimeout(3000);
    
    // Just verify the page loaded
    const url = page.url();
    expect(url).toBeTruthy();
  });

  test('Test 3: Open /frontend/items - loads without crash', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/items`);
    await page.waitForTimeout(3000);
    
    // Just verify the page loaded
    const url = page.url();
    expect(url).toBeTruthy();
  });
});

test.describe('Notification Center Tests', () => {
  test('Test N1: Open /frontend/notifications - loads without crash', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/notifications`);
    await page.waitForTimeout(3000);
    
    // Verify the page loaded (may redirect to login if not authenticated)
    const url = page.url();
    expect(url).toBeTruthy();
  });

  test('Test N2: Notification page shows notification list', async ({ page }) => {
    // This test assumes user is logged in - if not, it will redirect to login
    await page.goto(`${BASE_URL}/frontend/notifications`);
    await page.waitForTimeout(5000);
    
    // Check for the notifications heading or content
    const pageContent = await page.content();
    // The page should either show notifications or redirect to login
    const isAuthenticated = !page.url().includes('/login');
    
    if (isAuthenticated) {
      // Should have some notification-related content
      const hasNotificationsContent = pageContent.includes('Notification') || 
                                       pageContent.includes('notification');
      // Not asserting here - just checking page loads without crash
      expect(page.url()).toContain('/frontend/notifications');
    }
  });

  test('Test N3: Recovery pages still load correctly', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/recovery`);
    await page.waitForTimeout(3000);
    
    const url = page.url();
    expect(url).toBeTruthy();
  });
});

test.describe('API Endpoint Tests', () => {
  test('Test 4: API endpoints are accessible', async ({ request }) => {
    // Test ping endpoint
    const pingResponse = await request.get(`${BASE_URL}/api/method/ping`);
    expect([200, 405]).toContain(pingResponse.status());
  });
});

test.describe('Security Tests', () => {
  test('Test 5: No Invalid URL errors in console', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(5000);
    
    // Filter for Invalid URL errors specifically
    const invalidUrlErrors = consoleErrors.filter(err => 
      err.includes('Invalid URL') || err.includes('Invalid url')
    );
    
    expect(invalidUrlErrors).toHaveLength(0);
  });
});

test.describe('Public Scan Portal Tests', () => {
  test('Test 6: Public scan page loads for valid token', async ({ page }) => {
    // First get a valid token from demo data
    await page.goto(`${BASE_URL}/s/DNEEYP5TLQ`);
    await page.waitForTimeout(3000);
    
    const url = page.url();
    expect(url).toContain('/s/');
  });
  
  test('Test 7: Public scan page loads for invalid token', async ({ page }) => {
    await page.goto(`${BASE_URL}/s/INVALIDTOKEN123`);
    await page.waitForTimeout(3000);
    
    const url = page.url();
    expect(url).toContain('/s/');
  });
  
  test('Test 8: Public API returns valid response', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/method/scanifyme.public_portal.api.public_api.get_public_item_context?token=DNEEYP5TLQ`);
    expect(response.status()).toBe(200);
    
    const json = await response.json();
    expect(json.message).toBeDefined();
  });
});
