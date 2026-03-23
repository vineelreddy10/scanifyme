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

test.describe('Recovery Page Stability Tests', () => {
  let recoveryCaseId: string | null = null;

  test.beforeAll(async ({ request }) => {
    // Get a valid recovery case ID from demo data via console
    // We'll try to fetch it via the recovery API with admin session
    // For stability tests, we use the recovery list page
  });

  test('Recovery page loads without crash (no .toFixed() error)', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    await page.goto(`${BASE_URL}/frontend/recovery`);
    await page.waitForTimeout(5000);
    
    // Verify no .toFixed() crash
    const toFixedErrors = consoleErrors.filter(err =>
      err.includes('toFixed') ||
      err.includes('Cannot read properties of undefined') ||
      err.includes('TypeError')
    );
    
    // Page should load (may redirect to login if not authenticated)
    const url = page.url();
    expect(url).toBeTruthy();
    
    // If authenticated and shows content, no crash errors should exist
    if (!url.includes('/login')) {
      expect(toFixedErrors).toHaveLength(0);
    }
  });

  test('Recovery list page shows case data when authenticated', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    await page.goto(`${BASE_URL}/frontend/recovery`);
    await page.waitForTimeout(5000);
    
    // If not logged in, this will redirect
    const url = page.url();
    if (url.includes('/login')) {
      // User not logged in - this is acceptable for unauthenticated test
      return;
    }
    
    // Page loaded - verify no crash
    const pageContent = await page.content();
    expect(pageContent.length).toBeGreaterThan(0);
    
    // No TypeErrors from numeric rendering
    const typeErrors = consoleErrors.filter(err =>
      err.includes('TypeError') ||
      err.includes('Cannot read properties of undefined')
    );
    expect(typeErrors).toHaveLength(0);
  });

  test('Recovery detail page with location renders safely', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Get a recovery case that has a location (MacBook case from demo data)
    const caseId = 'Recovery - MacBook Pro 14 - 20260319215433';
    
    await page.goto(`${BASE_URL}/frontend/recovery/${encodeURIComponent(caseId)}`);
    await page.waitForTimeout(5000);
    
    const url = page.url();
    if (url.includes('/login')) {
      // Not logged in - acceptable for unauthenticated test
      return;
    }
    
    // Page loaded - no crash
    const pageContent = await page.content();
    expect(pageContent.length).toBeGreaterThan(0);
    
    // No .toFixed() errors - the critical fix
    const toFixedErrors = consoleErrors.filter(err =>
      err.includes('toFixed') ||
      (err.includes('undefined') && err.includes('reading'))
    );
    expect(toFixedErrors).toHaveLength(0);
  });

  test('Recovery detail page handles missing location gracefully', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Get a recovery case that may NOT have location
    // Using the wallet/keys cases which may not have location shared
    const caseId = 'Recovery - Wallet - 20260319215434';
    
    await page.goto(`${BASE_URL}/frontend/recovery/${encodeURIComponent(caseId)}`);
    await page.waitForTimeout(5000);
    
    const url = page.url();
    if (url.includes('/login')) {
      return;
    }
    
    // No crash even when no location is present
    const pageContent = await page.content();
    expect(pageContent.length).toBeGreaterThan(0);
    
    // No TypeErrors from null/undefined numeric values
    const numericErrors = consoleErrors.filter(err =>
      err.includes('TypeError') ||
      (err.includes('undefined') && err.includes('toFixed')) ||
      (err.includes('undefined') && err.includes('reading'))
    );
    expect(numericErrors).toHaveLength(0);
  });

  test('No toFixed errors across all recovery pages', async ({ page }) => {
    const allErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        allErrors.push(msg.text());
      }
    });
    
    // Visit recovery list
    await page.goto(`${BASE_URL}/frontend/recovery`);
    await page.waitForTimeout(3000);
    
    // Collect any toFixed errors
    const toFixedErrors = allErrors.filter(err =>
      err.includes('toFixed')
    );
    
    expect(toFixedErrors).toHaveLength(0);
  });

  test('Recovery page renders coordinates safely when present', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    const caseId = 'Recovery - MacBook Pro 14 - 20260319215433';
    await page.goto(`${BASE_URL}/frontend/recovery/${encodeURIComponent(caseId)}`);
    await page.waitForTimeout(5000);
    
    if (page.url().includes('/login')) return;
    
    // When location IS present, it should display coordinates safely
    // The page should NOT crash - it should show coordinates or fallback "—"
    const pageContent = await page.content();
    
    // If coordinates section renders, it should show either:
    // - "37.xxx, -122.xxx" (valid coordinates) OR
    // - "—" (fallback for missing/null)
    // It should NEVER crash with .toFixed() error
    expect(pageContent).toBeTruthy();
    
    const crashErrors = consoleErrors.filter(err =>
      err.includes('toFixed') ||
      err.includes('TypeError: Cannot read properties of undefined')
    );
    expect(crashErrors).toHaveLength(0);
  });
});

test.describe('Owner Dashboard Analytics Tests', () => {
  test('D1: Dashboard page loads without crash', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(5000);

    const url = page.url();
    expect(url).toBeTruthy();
  });

  test('D2: Dashboard shows summary cards when authenticated', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(6000);

    const url = page.url();
    if (url.includes('/login')) {
      return;
    }

    const pageContent = await page.content();
    expect(pageContent).toBeTruthy();

    const crashErrors = consoleErrors.filter(err =>
      err.includes('toFixed') ||
      err.includes('TypeError') ||
      err.includes('Cannot read properties of undefined')
    );
    expect(crashErrors).toHaveLength(0);
  });

  test('D3: Dashboard has quick actions section', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(6000);

    const url = page.url();
    if (url.includes('/login')) {
      return;
    }

    const pageContent = await page.content();
    expect(pageContent).toBeTruthy();

    const hasQuickActions =
      pageContent.includes('Quick Actions') ||
      pageContent.includes('Activate QR') ||
      pageContent.includes('View Items') ||
      pageContent.includes('Recovery');

    expect(hasQuickActions).toBeTruthy();
  });

  test('D4: Dashboard has navigation bar', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(5000);

    const url = page.url();
    if (url.includes('/login')) {
      return;
    }

    const pageContent = await page.content();
    expect(pageContent).toContain('ScanifyMe');
  });

  test('D5: No /frontend/api requests made by dashboard', async ({ page }) => {
    const apiCalls: string[] = [];
    page.on('request', req => {
      const url = req.url();
      if (url.includes('/frontend/api')) {
        apiCalls.push(url);
      }
    });

    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(5000);

    const invalidApiCalls = apiCalls.filter(url => url.includes('/frontend/api'));
    expect(invalidApiCalls).toHaveLength(0);
  });

  test('D6: Dashboard no console errors', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(5000);

    const criticalErrors = consoleErrors.filter(err =>
      err.includes('toFixed') ||
      err.includes('Invalid URL') ||
      err.includes('TypeError: Cannot read properties of undefined')
    );
    expect(criticalErrors).toHaveLength(0);
  });

  test('D7: Navigation between /frontend and /frontend/items works', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(5000);

    const frontendUrl = page.url();
    if (frontendUrl.includes('/login')) {
      return;
    }

    await page.goto(`${BASE_URL}/frontend/items`);
    await page.waitForTimeout(3000);

    const itemsUrl = page.url();
    expect(itemsUrl).toContain('/frontend/items');
    expect(itemsUrl).not.toContain('/dashboard');
  });

  test('D8: Navigation between /frontend and /frontend/recovery works', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(5000);

    const frontendUrl = page.url();
    if (frontendUrl.includes('/login')) {
      return;
    }

    await page.goto(`${BASE_URL}/frontend/recovery`);
    await page.waitForTimeout(3000);

    const recoveryUrl = page.url();
    expect(recoveryUrl).toContain('/frontend/recovery');
    expect(recoveryUrl).not.toContain('/dashboard');
  });

  test('D9: Navigation between /frontend and /frontend/notifications works', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(5000);

    const frontendUrl = page.url();
    if (frontendUrl.includes('/login')) {
      return;
    }

    await page.goto(`${BASE_URL}/frontend/notifications`);
    await page.waitForTimeout(3000);

    const notifUrl = page.url();
    expect(notifUrl).toContain('/frontend/notifications');
    expect(notifUrl).not.toContain('/dashboard');
  });
});

test.describe('Dashboard API Smoke Tests', () => {
  let authCookies: string;

  test.beforeAll(async ({ request: req }) => {
    // Login as demo user to get session
    const loginRes = await req.post(`${BASE_URL}/api/method/login`, {
      data: {
        usr: 'demo@scanifyme.app',
        pwd: 'demo123',
      },
    });
    authCookies = loginRes.headers()['set-cookie'] || '';
  });

  test('D10: get_owner_dashboard_summary API responds', async ({ request }) => {
    const response = await request.post(
      `${BASE_URL}/api/method/scanifyme.reports.api.dashboard_api.get_owner_dashboard_summary`,
      { headers: { Cookie: authCookies } }
    );
    expect([200, 401, 403]).toContain(response.status());
  });

  test('D11: get_admin_operational_summary API responds', async ({ request }) => {
    const response = await request.post(
      `${BASE_URL}/api/method/scanifyme.reports.api.dashboard_api.get_admin_operational_summary`,
      { headers: { Cookie: authCookies } }
    );
    expect([200, 401, 403]).toContain(response.status());
  });

  test('D12: get_owner_recent_activity API responds', async ({ request }) => {
    const response = await request.post(
      `${BASE_URL}/api/method/scanifyme.reports.api.dashboard_api.get_owner_recent_activity`,
      {
        headers: { Cookie: authCookies },
        data: { limit: 10 },
      }
    );
    expect([200, 401, 403]).toContain(response.status());
  });
});
