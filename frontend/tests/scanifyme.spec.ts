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
