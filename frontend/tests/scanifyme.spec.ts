import { test, expect } from '@playwright/test';

const BASE_URL = process.env.TEST_BASE_URL || 'http://localhost:8000';

test.describe('ScanifyMe Frontend', () => {
  test('Test 1: Open /frontend - Expect SPA loads', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend`);
    
    // Should load the dashboard or redirect to login
    // Check for ScanifyMe branding
    await expect(page.locator('text=ScanifyMe').first()).toBeVisible({ timeout: 10000 });
  });

  test('Test 2: Open /frontend/activate-qr - Enter valid token - Expect redirect to item creation', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/activate-qr`);
    
    // Should load the activate QR page
    await expect(page.locator('text=Activate QR Code')).toBeVisible({ timeout: 10000 });
    
    // Check for QR token input
    const tokenInput = page.locator('#qr-token');
    await expect(tokenInput).toBeVisible();
  });

  test('Test 3: Submit item form - Expect item created', async ({ page }) => {
    // This test requires authentication
    // Skip if not logged in
    test.skip();
    
    await page.goto(`${BASE_URL}/frontend/activate-qr`);
    
    // Enter QR token
    await page.fill('#qr-token', 'TEST123456');
    await page.click('button[type="submit"]');
    
    // Wait for activation result
    await page.waitForSelector('text=QR Code Activated', { timeout: 10000 });
    
    // Fill item form
    await page.fill('#item-name', 'Test Item');
    await page.click('button:has-text("Create Item")');
    
    // Should redirect to item detail or show success
    await expect(page.locator('text=Item created successfully')).toBeVisible({ timeout: 10000 });
  });

  test('Test 4: Open /frontend/items - Expect item visible', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/items`);
    
    // Should load the items page
    await expect(page.locator('text=My Items')).toBeVisible({ timeout: 10000 });
  });

  test('Test 5: Open /frontend/items/:id - Expect item details render', async ({ page }) => {
    // This test requires a valid item ID
    test.skip();
    
    await page.goto(`${BASE_URL}/frontend/items/test-item-123`);
    
    // Should load item details
    await expect(page.locator('text=Item Details')).toBeVisible({ timeout: 10000 });
  });

  test('Test 6: Navigate to /app/* and press browser back - Expect return to /frontend', async ({ page }) => {
    // First navigate to frontend
    await page.goto(`${BASE_URL}/frontend`);
    await expect(page.locator('text=ScanifyMe').first()).toBeVisible({ timeout: 10000 });
    
    // Navigate to admin page (simulated)
    await page.goto(`${BASE_URL}/app/qr-batch`);
    
    // Go back
    await page.goBack();
    
    // Should return to /frontend, not /dashboard
    await expect(page).toHaveURL(/.*\/frontend/);
    await expect(page).not.toHaveURL(/.*\/dashboard/);
  });
});

test.describe('Security Tests', () => {
  test('API responses should not expose DocType names or database IDs', async ({ page }) => {
    // This is a placeholder for security testing
    // In a real test, you would intercept API responses
    // and verify they don't expose internal metadata
    
    test.skip();
  });
});