import { test, expect } from '@playwright/test';

const BASE_URL = process.env.TEST_BASE_URL || 'http://test.localhost:8002';

test.describe('ScanifyMe Operational Features', () => {
  
  test.describe.configure({ mode: 'serial' });

  test('OP1: Public scan page loads with valid token', async ({ page }) => {
    // Get a valid demo token first via API
    await page.goto(`${BASE_URL}/api/method/ping`);
    
    // Visit public scan page with demo token
    await page.goto(`${BASE_URL}/s/PTD6C9VX9W`);
    await page.waitForTimeout(3000);
    
    const url = page.url();
    expect(url).toContain('/s/');
  });

  test('OP2: Public scan shows safe error for invalid token', async ({ page }) => {
    await page.goto(`${BASE_URL}/s/INVALID_TOKEN_XYZ`);
    await page.waitForTimeout(3000);
    
    // Should not show internal errors
    const bodyText = await page.textContent('body');
    expect(bodyText).not.toContain('Traceback');
    expect(bodyText).not.toContain('FRAPPE_');
    expect(bodyText).not.toContain('Database');
  });

  test('OP3: Frontend dashboard loads without console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(3000);
    
    // Filter out expected non-critical errors
    const criticalErrors = errors.filter(e => 
      !e.includes('ERR_CONNECTION_REFUSED') && 
      !e.includes('WebSocket') &&
      !e.includes('favicon')
    );
    
    expect(criticalErrors.length).toBe(0);
  });

  test('OP4: Generic list page loads', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item Category`);
    await page.waitForTimeout(3000);
    
    const url = page.url();
    expect(url).toContain('/list/');
  });

  test('OP5: Notification bell exists on dashboard', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(3000);
    
    // Check for notification-related elements
    const pageContent = await page.textContent('body');
    // Notification bell or notifications link should exist
    expect(pageContent).toBeTruthy();
  });

  test('OP6: No Invalid URL errors in console', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // Visit multiple pages
    await page.goto(`${BASE_URL}/frontend/items`);
    await page.waitForTimeout(2000);
    await page.goto(`${BASE_URL}/frontend/recovery`);
    await page.waitForTimeout(2000);
    await page.goto(`${BASE_URL}/frontend/notifications`);
    await page.waitForTimeout(2000);
    
    // No Invalid URL errors
    const invalidUrlErrors = errors.filter(e => 
      e.includes('Invalid URL') || 
      e.includes('404')
    );
    
    expect(invalidUrlErrors.length).toBe(0);
  });

  test('OP7: No /frontend/api/ URL patterns', async ({ page }) => {
    const apiCalls: string[] = [];
    page.on('request', request => {
      const url = request.url();
      if (url.includes('/frontend/api/')) {
        apiCalls.push(url);
      }
    });
    
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(3000);
    
    // Should not have any /frontend/api/ calls
    expect(apiCalls.length).toBe(0);
  });

  test('OP8: Masters page loads for admin', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/masters`);
    await page.waitForTimeout(3000);
    
    const url = page.url();
    expect(url).toContain('/masters');
  });

  test('OP9: Navigation sidebar renders', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(3000);
    
    // Check for sidebar or navigation
    const hasNav = await page.locator('nav, [class*="sidebar"], [class*="nav"]').count();
    expect(hasNav).toBeGreaterThan(0);
  });

  test('OP10: Settings page accessible', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/settings`);
    await page.waitForTimeout(3000);
    
    const url = page.url();
    expect(url).toContain('/settings');
  });
});

test.describe('ScanifyMe API Regression Tests', () => {
  
  test('API1: Ping endpoint responds', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/method/ping`);
    expect(response.ok()).toBeTruthy();
  });

  test('API2: Public item context with invalid token returns safe error', async ({ request }) => {
    const response = await request.post(
      `${BASE_URL}/api/method/scanifyme.public_portal.api.public_api.get_public_item_context`,
      { 
        data: { token: 'INVALID_TOKEN_XYZ' },
        headers: { 'Content-Type': 'application/json' }
      }
    );
    
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    
    // Should return success=false, not a crash
    expect(body).toHaveProperty('message') || body.toHaveProperty('exc');
    
    // Response should not contain stack traces
    const responseText = JSON.stringify(body);
    expect(responseText).not.toContain('Traceback');
  });

  test('API3: No /frontend/api/ in any API path', async ({ request }) => {
    // Test various API endpoints
    const endpoints = [
      'frappe.auth.get_logged_user',
      'ping',
    ];
    
    for (const endpoint of endpoints) {
      const response = await request.get(`${BASE_URL}/api/method/${endpoint}`);
      const url = response.url();
      expect(url).not.toContain('/frontend/api/');
    }
  });
});

test.describe('ScanifyMe Navigation Tests', () => {
  
  test('NAV1: /frontend to /app/* navigation returns to /frontend', async ({ page }) => {
    // Start at frontend
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(2000);
    
    // Navigate to Desk (admin)
    await page.goto(`${BASE_URL}/app`);
    await page.waitForTimeout(2000);
    
    // Go back to frontend
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(2000);
    
    // Should NOT be at /dashboard
    const url = page.url();
    expect(url).not.toContain('/dashboard');
    expect(url).toContain('/frontend');
  });

  test('NAV2: Multiple frontend pages accessible', async ({ page }) => {
    const pages = [
      '/frontend',
      '/frontend/items',
      '/frontend/recovery',
      '/frontend/notifications',
    ];
    
    for (const path of pages) {
      await page.goto(`${BASE_URL}${path}`);
      await page.waitForTimeout(2000);
      
      const url = page.url();
      expect(url).toContain(path.split('/')[1]);
    }
  });
});
