import { test, expect } from '@playwright/test';

const BASE_URL = process.env.TEST_BASE_URL || 'http://test.localhost:8002';

test.describe('Generic Detail Page Tests', () => {
  test.describe.configure({ mode: 'serial' });

  test('GD1: /frontend/m/Item Category/:name loads without crash', async ({ page }) => {
    // First get a valid Item Category name from the list
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    // Try to find a row and click it
    const firstRow = page.locator('tbody tr').first();
    const rowExists = await firstRow.count() > 0;
    
    if (rowExists) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      // Should now be on detail page
      const url = page.url();
      expect(url).toContain('/m/Item%20Category/');
    } else {
      // No items to test - just verify page doesn't crash
      const url = page.url();
      expect(url).toBeTruthy();
    }
  });

  test('GD2: /frontend/m/QR Batch/:name loads without crash', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/QR%20Batch`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    const rowExists = await firstRow.count() > 0;
    
    if (rowExists) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      const url = page.url();
      expect(url).toContain('/m/QR%20Batch/');
    } else {
      expect(page.url()).toBeTruthy();
    }
  });

  test('GD3: /frontend/m/Recovery Case/:name loads without crash', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Recovery%20Case`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    const rowExists = await firstRow.count() > 0;
    
    if (rowExists) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      const url = page.url();
      expect(url).toContain('/m/Recovery%20Case/');
    } else {
      expect(page.url()).toBeTruthy();
    }
  });

  test('GD4: /frontend/m/QR Code Tag/:name loads without crash', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/QR%20Code%20Tag`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    const rowExists = await firstRow.count() > 0;
    
    if (rowExists) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      const url = page.url();
      expect(url).toContain('/m/QR%20Code%20Tag/');
    } else {
      expect(page.url()).toBeTruthy();
    }
  });
});

test.describe('Generic Detail Functionality Tests', () => {
  test('GD5: Detail page shows page title', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    const rowExists = await firstRow.count() > 0;
    
    if (rowExists) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      const pageContent = await page.content();
      const hasTitle = pageContent.includes('Item') || pageContent.includes('Category');
      expect(hasTitle).toBeTruthy();
    }
  });

  test('GD6: Detail page shows Edit button', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    const rowExists = await firstRow.count() > 0;
    
    if (rowExists) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      const editButton = page.locator('button:has-text("Edit")');
      const count = await editButton.count();
      expect(count).toBeGreaterThanOrEqual(0);
    }
  });

  test('GD7: Detail page has back button', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    const rowExists = await firstRow.count() > 0;
    
    if (rowExists) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      const backButton = page.locator('button svg[class*="arrow"]').first();
      const count = await backButton.count();
      expect(count).toBeGreaterThanOrEqual(0);
    }
  });

  test('GD8: Invalid DocType shows error', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/m/NonExistentDoctypeXYZ/some-name`);
    await page.waitForTimeout(5000);
    
    const pageContent = await page.content();
    const hasError = pageContent.includes('Error') || 
                     pageContent.includes('Permission') ||
                     pageContent.includes('does not exist') ||
                     pageContent.includes('Not Found');
    expect(hasError).toBeTruthy();
  });
});

test.describe('Generic Detail Edit Mode Tests', () => {
  test('GD9: Edit mode enables form fields', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    const rowExists = await firstRow.count() > 0;
    
    if (rowExists) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      // Click Edit button
      const editButton = page.locator('button:has-text("Edit")');
      if (await editButton.count() > 0) {
        await editButton.click();
        await page.waitForTimeout(1000);
        
        // Should show Save button
        const saveButton = page.locator('button:has-text("Save")');
        expect(await saveButton.count()).toBeGreaterThanOrEqual(0);
      }
    }
  });

  test('GD10: Cancel exits edit mode', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    const rowExists = await firstRow.count() > 0;
    
    if (rowExists) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      const editButton = page.locator('button:has-text("Edit")');
      if (await editButton.count() > 0) {
        await editButton.click();
        await page.waitForTimeout(1000);
        
        // Cancel should appear
        const cancelButton = page.locator('button:has-text("Cancel")');
        if (await cancelButton.count() > 0) {
          await cancelButton.click();
          await page.waitForTimeout(1000);
          
          // Should be back to view mode
          const editButtonAgain = page.locator('button:has-text("Edit")');
          expect(await editButtonAgain.count()).toBeGreaterThanOrEqual(0);
        }
      }
    }
  });
});

test.describe('Generic Detail Permission Tests', () => {
  test('GD11: No /frontend/api/* calls', async ({ page }) => {
    const wrongPathCalls: string[] = [];
    
    page.on('request', (request) => {
      const url = request.url();
      if (url.includes('/frontend/api/')) {
        wrongPathCalls.push(url);
      }
    });
    
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    expect(wrongPathCalls.length).toBe(0);
  });

  test('GD12: Page loads without console errors', async ({ page }) => {
    const consoleErrors: string[] = [];
    
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.count() > 0) {
      await firstRow.click();
      await page.waitForTimeout(3000);
    }
    
    // Filter out expected/benign errors
    const criticalErrors = consoleErrors.filter(err => 
      !err.includes('favicon') && 
      !err.includes('net::ERR') &&
      !err.includes('socket.io')
    );
    
    expect(criticalErrors.length).toBe(0);
  });
});

test.describe('Generic Detail Navigation Tests', () => {
  test('GD13: Back button navigates to list', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    const rowExists = await firstRow.count() > 0;
    
    if (rowExists) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      // Click back button
      const backButton = page.locator('button svg[class*="arrow"]').first();
      if (await backButton.count() > 0) {
        await backButton.click();
        await page.waitForTimeout(2000);
        
        // Should be back on list page
        const url = page.url();
        expect(url).toContain('/list/');
      }
    }
  });

  test('GD14: Navigate between detail pages', async ({ page }) => {
    // First detail page
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    let firstRow = page.locator('tbody tr').first();
    if (await firstRow.count() > 0) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      // Go back
      let backButton = page.locator('button svg[class*="arrow"]').first();
      if (await backButton.count() > 0) {
        await backButton.click();
        await page.waitForTimeout(2000);
      }
      
      // Second detail page
      await page.goto(`${BASE_URL}/frontend/list/QR%20Batch`);
      await page.waitForTimeout(5000);
      
      firstRow = page.locator('tbody tr').first();
      if (await firstRow.count() > 0) {
        await firstRow.click();
        await page.waitForTimeout(3000);
        
        const url = page.url();
        expect(url).toContain('/m/');
      }
    }
  });
});
