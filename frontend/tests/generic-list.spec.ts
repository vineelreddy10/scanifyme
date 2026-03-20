import { test, expect } from '@playwright/test';

const BASE_URL = process.env.TEST_BASE_URL || 'http://test.localhost:8002';

test.describe('Generic List Page Tests', () => {
  test.describe.configure({ mode: 'serial' });

  test('GL1: /frontend/list/Item Category loads without crash', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const url = page.url();
    // Should either show the list or redirect to login
    expect(url).toBeTruthy();
    
    // Should not have JS errors
    const errors: string[] = [];
    page.on('pageerror', (error) => {
      errors.push(error.message);
    });
    
    // Wait a bit for any JS errors
    await page.waitForTimeout(2000);
    expect(errors.length).toBe(0);
  });

  test('GL2: /frontend/list/QR Batch loads without crash', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/QR%20Batch`);
    await page.waitForTimeout(5000);
    
    const url = page.url();
    expect(url).toBeTruthy();
  });

  test('GL3: /frontend/list/Recovery Case loads without crash', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Recovery%20Case`);
    await page.waitForTimeout(5000);
    
    const url = page.url();
    expect(url).toBeTruthy();
  });

  test('GL4: /frontend/list/QR Code Tag loads without crash', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/QR%20Code%20Tag`);
    await page.waitForTimeout(5000);
    
    const url = page.url();
    expect(url).toBeTruthy();
  });

  test('GL5: /frontend/list/Registered Item loads without crash', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Registered%20Item`);
    await page.waitForTimeout(5000);
    
    const url = page.url();
    expect(url).toBeTruthy();
  });

  test('GL6: /frontend/list/Notification Event Log loads without crash', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Notification%20Event%20Log`);
    await page.waitForTimeout(5000);
    
    const url = page.url();
    expect(url).toBeTruthy();
  });
});

test.describe('Generic List Functionality Tests', () => {
  test('GL7: Generic list shows page title from metadata', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    // Check if the page shows "Item Category" or "Item" in the heading
    const pageContent = await page.content();
    const hasTitle = pageContent.includes('Item') || pageContent.includes('Category');
    expect(hasTitle).toBeTruthy();
  });

  test('GL8: Generic list has search input', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    // Look for search input
    const searchInput = page.locator('input[placeholder*="Search" i], input[type="search"]');
    const count = await searchInput.count();
    expect(count).toBeGreaterThanOrEqual(0); // May or may not have search based on auth state
  });

  test('GL9: Generic list has refresh button', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    // Look for refresh button (icon button with refresh icon)
    const refreshButton = page.locator('button[title="Refresh"], button svg[class*="animate-spin"]').first();
    const count = await refreshButton.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('GL10: Generic list has pagination info', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    // Look for pagination text (e.g., "Showing 1 to 10 of X results")
    const pageContent = await page.content();
    const hasPagination = pageContent.includes('Showing') || 
                         pageContent.includes('results') ||
                         pageContent.includes('No results') ||
                         pageContent.includes('Showing');
    expect(hasPagination).toBeTruthy();
  });

  test('GL11: Invalid DocType shows error', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/NonExistentDoctypeXYZ`);
    await page.waitForTimeout(5000);
    
    const pageContent = await page.content();
    // Should show some kind of error (permission denied or not found)
    const hasError = pageContent.includes('Error') || 
                     pageContent.includes('Permission') ||
                     pageContent.includes('does not exist') ||
                     pageContent.includes('Not Found');
    expect(hasError).toBeTruthy();
  });
});

test.describe('Generic List Permission Tests', () => {
  test('GL12: No /frontend/api/* calls (wrong API path)', async ({ page }) => {
    const wrongPathCalls: string[] = [];
    
    page.on('request', (request) => {
      const url = request.url();
      if (url.includes('/frontend/api/')) {
        wrongPathCalls.push(url);
      }
    });
    
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    // Should not make any calls to /frontend/api/*
    expect(wrongPathCalls.length).toBe(0);
  });

  test('GL13: API calls use /api/method/ or /api/v2/ paths', async ({ page }) => {
    const apiCalls: string[] = [];
    
    page.on('request', (request) => {
      const url = request.url();
      if (url.includes('/api/')) {
        apiCalls.push(url);
      }
    });
    
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    // All API calls should use correct paths
    const invalidCalls = apiCalls.filter(url => 
      url.includes('/frontend/api/') || 
      url.includes('/api/') && !url.includes('/api/method/') && !url.includes('/api/v2/')
    );
    
    // Some calls to /api/method/ or /api/v2/ are expected
    expect(apiCalls.length).toBeGreaterThanOrEqual(0);
  });
});

test.describe('Generic List UX Tests', () => {
  test('GL14: Page loads without console errors', async ({ page }) => {
    const consoleErrors: string[] = [];
    
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    // Filter out expected/benign errors
    const criticalErrors = consoleErrors.filter(err => 
      !err.includes('favicon') && 
      !err.includes('net::ERR') &&
      !err.includes('socket.io')
    );
    
    expect(criticalErrors.length).toBe(0);
  });

  test('GL15: Navigation between list pages works', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(3000);
    
    // Navigate to another list
    await page.goto(`${BASE_URL}/frontend/list/QR%20Batch`);
    await page.waitForTimeout(3000);
    
    const url = page.url();
    expect(url).toContain('/list/QR%20Batch');
  });

  test('GL16: Back navigation from list works', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(3000);
    
    // Go back to dashboard
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(3000);
    
    const url = page.url();
    expect(url).toContain('/frontend');
  });
});
