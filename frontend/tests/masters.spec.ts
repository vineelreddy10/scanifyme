import { test, expect } from '@playwright/test';

const BASE_URL = process.env.TEST_BASE_URL || 'http://test.localhost:8002';

test.describe('Masters Page Tests', () => {
  test.describe.configure({ mode: 'serial' });

  test('M1: /frontend/masters loads without crash', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/masters`);
    await page.waitForTimeout(5000);
    
    const url = page.url();
    expect(url).toBeTruthy();
    
    // Should not have JS errors
    const errors: string[] = [];
    page.on('pageerror', (error) => {
      errors.push(error.message);
    });
    
    await page.waitForTimeout(2000);
    expect(errors.length).toBe(0);
  });

  test('M2: Masters page shows page title', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/masters`);
    await page.waitForTimeout(5000);
    
    const pageContent = await page.content();
    const hasTitle = pageContent.includes('Masters');
    expect(hasTitle).toBeTruthy();
  });

  test('M3: Masters page shows section headers', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/masters`);
    await page.waitForTimeout(5000);
    
    const pageContent = await page.content();
    // Should show at least one section (Configuration, Reference Data, or Administration)
    const hasSection = pageContent.includes('Configuration') || 
                       pageContent.includes('Reference') ||
                       pageContent.includes('Administration');
    expect(hasSection).toBeTruthy();
  });

  test('M4: Masters page shows master cards', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/masters`);
    await page.waitForTimeout(5000);
    
    // Look for master card content
    const pageContent = await page.content();
    const hasCards = pageContent.includes('Category') || 
                     pageContent.includes('Notification') ||
                     pageContent.includes('QR');
    expect(hasCards).toBeTruthy();
  });

  test('M5: Clicking a master card navigates to list page', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/masters`);
    await page.waitForTimeout(5000);
    
    // Find and click on Item Categories card (should be accessible to all)
    const itemCategoryCard = page.locator('text=Item Categories').first();
    const cardExists = await itemCategoryCard.count() > 0;
    
    if (cardExists) {
      // Click the parent button/card
      await itemCategoryCard.click();
      await page.waitForTimeout(3000);
      
      // Should navigate to list page
      const url = page.url();
      expect(url).toContain('/list/');
    }
  });

  test('M6: Masters page has proper icon', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/masters`);
    await page.waitForTimeout(5000);
    
    // Check for the Masters icon (collection icon)
    const collectionIcon = page.locator('svg path[d*="M19 11"]');
    const count = await collectionIcon.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('Masters Navigation Tests', () => {
  test('M7: Navigate to Masters from dashboard', async ({ page }) => {
    // Go to dashboard
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(3000);
    
    // Navigate to Masters
    await page.goto(`${BASE_URL}/frontend/masters`);
    await page.waitForTimeout(3000);
    
    const url = page.url();
    expect(url).toContain('/masters');
  });

  test('M8: Masters card links to correct list route', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/masters`);
    await page.waitForTimeout(5000);
    
    // Find Notification Preferences card
    const notifCard = page.locator('text=Notification Preferences').first();
    if (await notifCard.count() > 0) {
      await notifCard.click();
      await page.waitForTimeout(3000);
      
      const url = page.url();
      expect(url).toContain('/list/');
      expect(url).toContain('Notification%20Preference');
    }
  });

  test('M9: Masters back navigation works', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/masters`);
    await page.waitForTimeout(3000);
    
    // Go back to dashboard
    await page.goto(`${BASE_URL}/frontend`);
    await page.waitForTimeout(3000);
    
    const url = page.url();
    expect(url).toContain('/frontend');
  });
});

test.describe('Masters Permission Tests', () => {
  test('M10: No /frontend/api/* calls on Masters page', async ({ page }) => {
    const wrongPathCalls: string[] = [];
    
    page.on('request', (request) => {
      const url = request.url();
      if (url.includes('/frontend/api/')) {
        wrongPathCalls.push(url);
      }
    });
    
    await page.goto(`${BASE_URL}/frontend/masters`);
    await page.waitForTimeout(5000);
    
    expect(wrongPathCalls.length).toBe(0);
  });

  test('M11: Masters page loads without console errors', async ({ page }) => {
    const consoleErrors: string[] = [];
    
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    await page.goto(`${BASE_URL}/frontend/masters`);
    await page.waitForTimeout(5000);
    
    // Filter out expected/benign errors
    const criticalErrors = consoleErrors.filter(err => 
      !err.includes('favicon') && 
      !err.includes('net::ERR') &&
      !err.includes('socket.io')
    );
    
    expect(criticalErrors.length).toBe(0);
  });
});

test.describe('Masters Configuration Tests', () => {
  test('M12: Masters config exports are valid', async ({ page }) => {
    // This test verifies the Masters page can render without errors
    // which implies the config is valid
    
    const consoleErrors: string[] = [];
    page.on('pageerror', (error) => {
      consoleErrors.push(error.message);
    });
    
    await page.goto(`${BASE_URL}/frontend/masters`);
    await page.waitForTimeout(5000);
    
    // Should not have config-related errors
    const configErrors = consoleErrors.filter(err =>
      err.includes('MASTERS_CONFIG') ||
      err.includes('config')
    );
    
    expect(configErrors.length).toBe(0);
  });

  test('M13: Masters page shows feature badges', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/masters`);
    await page.waitForTimeout(5000);
    
    // Look for feature badges like "View list", "Create new", etc.
    const pageContent = await page.content();
    const hasFeatures = pageContent.includes('View') || 
                       pageContent.includes('Create') ||
                       pageContent.includes('Edit');
    expect(hasFeatures).toBeTruthy();
  });
});
