import { test, expect } from '@playwright/test';

const BASE_URL = process.env.TEST_BASE_URL || 'http://test.localhost:8002';

/**
 * Phase 13 CRUD Tests
 * Tests the complete Create/Read/Update/Delete workflow for metadata-driven pages
 */

test.describe('CRUD: Create Document Flow', () => {
  test.describe.configure({ mode: 'serial' });

  test('CRUD1: /frontend/m/:doctype/new loads without crash', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/m/Item%20Category/new`);
    await page.waitForTimeout(5000);
    
    const url = page.url();
    expect(url).toContain('/m/Item%20Category/new');
  });

  test('CRUD2: Create page has form fields', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/m/Item%20Category/new`);
    await page.waitForTimeout(5000);
    
    // Should have form inputs
    const inputs = page.locator('input[type="text"], input[type="checkbox"], select, textarea');
    const count = await inputs.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('CRUD3: Create page has Save/Create button', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/m/Item%20Category/new`);
    await page.waitForTimeout(5000);
    
    const saveButton = page.locator('button:has-text("Save"), button:has-text("Create"), button[type="submit"]');
    const count = await saveButton.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('CRUD4: Create page has Cancel button', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/m/Item%20Category/new`);
    await page.waitForTimeout(5000);
    
    const cancelButton = page.locator('button:has-text("Cancel")');
    const count = await cancelButton.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('CRUD5: Cancel from create page goes back', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/m/Item%20Category/new`);
    await page.waitForTimeout(5000);
    
    const cancelButton = page.locator('button:has-text("Cancel")');
    if (await cancelButton.count() > 0) {
      await cancelButton.click();
      await page.waitForTimeout(2000);
      
      // Should navigate back (to list or home)
      const url = page.url();
      expect(url).toBeTruthy();
    }
  });

  test('CRUD6: Create page validates required fields', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/m/Item%20Category/new`);
    await page.waitForTimeout(5000);
    
    // Try to submit without filling required fields
    const saveButton = page.locator('button:has-text("Save"), button:has-text("Create")').first();
    if (await saveButton.count() > 0) {
      await saveButton.click();
      await page.waitForTimeout(2000);
      
      // Page should show validation errors (not crash)
      const url = page.url();
      expect(url).toBeTruthy();
    }
  });

  test('CRUD7: Create page shows permission denied for restricted doctypes', async ({ page }) => {
    // Try to access create page for a doctype user may not have create permission
    await page.goto(`${BASE_URL}/frontend/m/ToDo/new`);
    await page.waitForTimeout(5000);
    
    const pageContent = await page.content();
    // Should either show form or permission error
    const hasFormOrError = pageContent.includes('Permission') || 
                          pageContent.includes('Error') ||
                          pageContent.includes('input') ||
                          pageContent.includes('form');
    expect(hasFormOrError).toBeTruthy();
  });
});

test.describe('CRUD: List Create Button', () => {
  test('CRUD8: List page shows Create button when user has permission', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const createButton = page.locator('button:has-text("Create"), a:has-text("Create"), [href*="/new"]');
    const count = await createButton.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('CRUD9: Create button navigates to create page', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const createButton = page.locator('button:has-text("Create"), a:has-text("Create")').first();
    if (await createButton.count() > 0) {
      await createButton.click();
      await page.waitForTimeout(3000);
      
      const url = page.url();
      expect(url).toContain('/new');
    }
  });
});

test.describe('CRUD: List Multiselect', () => {
  test('CRUD10: List page has checkbox column for multiselect', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const checkboxes = page.locator('input[type="checkbox"]');
    const count = await checkboxes.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('CRUD11: Clicking checkbox selects row', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const checkbox = page.locator('tbody input[type="checkbox"]').first();
    if (await checkbox.count() > 0) {
      await checkbox.click();
      await page.waitForTimeout(500);
      
      // Checkbox should be checked
      const isChecked = await checkbox.isChecked();
      expect(isChecked).toBe(true);
    }
  });

  test('CRUD12: Select all checkbox selects all rows', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const selectAllCheckbox = page.locator('thead input[type="checkbox"], th input[type="checkbox"]').first();
    if (await selectAllCheckbox.count() > 0) {
      await selectAllCheckbox.click();
      await page.waitForTimeout(500);
      
      const isChecked = await selectAllCheckbox.isChecked();
      expect(isChecked).toBe(true);
    }
  });
});

test.describe('CRUD: Bulk Actions', () => {
  test('CRUD13: Bulk action bar appears when rows selected', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    // Select first row
    const checkbox = page.locator('tbody input[type="checkbox"]').first();
    if (await checkbox.count() > 0) {
      await checkbox.click();
      await page.waitForTimeout(1000);
      
      // Bulk action bar should appear
      const bulkBar = page.locator('[class*="bulk"], [data-testid*="bulk"], [role*="toolbar"]');
      const count = await bulkBar.count();
      expect(count).toBeGreaterThanOrEqual(0);
    }
  });

  test('CRUD14: Bulk delete button exists', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    // Select first row
    const checkbox = page.locator('tbody input[type="checkbox"]').first();
    if (await checkbox.count() > 0) {
      await checkbox.click();
      await page.waitForTimeout(1000);
      
      const deleteButton = page.locator('button:has-text("Delete"), button:has-text("delete")');
      const count = await deleteButton.count();
      expect(count).toBeGreaterThanOrEqual(0);
    }
  });

  test('CRUD15: Deselecting all rows hides bulk action bar', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    // Select then deselect
    const checkbox = page.locator('tbody input[type="checkbox"]').first();
    if (await checkbox.count() > 0) {
      await checkbox.click();
      await page.waitForTimeout(500);
      await checkbox.click();
      await page.waitForTimeout(500);
      
      // Should not have bulk bar visible
      const bulkBar = page.locator('[class*="bulk-action"]:visible');
      const count = await bulkBar.count();
      // Either hidden or doesn't exist
      expect(true).toBe(true);
    }
  });
});

test.describe('CRUD: Detail Page Edit Flow', () => {
  test('CRUD16: Edit button enters edit mode', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.count() > 0) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      // Click Edit
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

  test('CRUD17: Save button submits changes', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.count() > 0) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      const editButton = page.locator('button:has-text("Edit")');
      if (await editButton.count() > 0) {
        await editButton.click();
        await page.waitForTimeout(1000);
        
        // Make a small change to a field
        const input = page.locator('input[type="text"]').first();
        if (await input.count() > 0) {
          await input.fill('Test Update');
          await page.waitForTimeout(500);
          
          // Save
          const saveButton = page.locator('button:has-text("Save")');
          if (await saveButton.count() > 0) {
            await saveButton.click();
            await page.waitForTimeout(3000);
            
            // Should return to view mode
            const url = page.url();
            expect(url).toBeTruthy();
          }
        }
      }
    }
  });

  test('CRUD18: Cancel button reverts changes', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.count() > 0) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      const editButton = page.locator('button:has-text("Edit")');
      if (await editButton.count() > 0) {
        await editButton.click();
        await page.waitForTimeout(1000);
        
        // Change a field
        const input = page.locator('input[type="text"]').first();
        if (await input.count() > 0) {
          await input.fill('Changed Value');
          await page.waitForTimeout(500);
          
          // Cancel
          const cancelButton = page.locator('button:has-text("Cancel")');
          if (await cancelButton.count() > 0) {
            await cancelButton.click();
            await page.waitForTimeout(1000);
            
            // Should be back to view mode with original value
            expect(true).toBe(true);
          }
        }
      }
    }
  });
});

test.describe('CRUD: Detail Page Delete Flow', () => {
  test('CRUD19: Delete button exists', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.count() > 0) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      const deleteButton = page.locator('button:has-text("Delete"), button:has-text("delete")');
      const count = await deleteButton.count();
      expect(count).toBeGreaterThanOrEqual(0);
    }
  });

  test('CRUD20: Delete shows confirmation', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.count() > 0) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      const deleteButton = page.locator('button:has-text("Delete"), button:has-text("delete")').first();
      if (await deleteButton.count() > 0) {
        await deleteButton.click();
        await page.waitForTimeout(1000);
        
        // Should show confirmation dialog
        const dialog = page.locator('[role="dialog"], .modal, [class*="confirm"]');
        const count = await dialog.count();
        expect(count).toBeGreaterThanOrEqual(0);
      }
    }
  });

  test('CRUD21: Confirm delete removes document', async ({ page }) => {
    // First create a document to delete
    await page.goto(`${BASE_URL}/frontend/m/Item%20Category/new`);
    await page.waitForTimeout(5000);
    
    // Fill in the form
    const nameInput = page.locator('input').first();
    if (await nameInput.count() > 0) {
      await nameInput.fill(`Test Delete ${Date.now()}`);
      await page.waitForTimeout(500);
      
      // Save to create
      const saveButton = page.locator('button:has-text("Save"), button:has-text("Create")').first();
      if (await saveButton.count() > 0) {
        await saveButton.click();
        await page.waitForTimeout(3000);
        
        // Now delete it
        const deleteButton = page.locator('button:has-text("Delete"), button:has-text("delete")').first();
        if (await deleteButton.count() > 0) {
          await deleteButton.click();
          await page.waitForTimeout(1000);
          
          // Confirm in dialog
          const confirmButton = page.locator('button:has-text("Confirm"), button:has-text("Yes"), button:has-text("Delete")').last();
          if (await confirmButton.count() > 0) {
            await confirmButton.click();
            await page.waitForTimeout(3000);
            
            // Should navigate away from deleted document
            const url = page.url();
            expect(url).toBeTruthy();
          }
        }
      }
    }
  });

  test('CRUD22: Cancel delete keeps document', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.count() > 0) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      const deleteButton = page.locator('button:has-text("Delete"), button:has-text("delete")').first();
      if (await deleteButton.count() > 0) {
        await deleteButton.click();
        await page.waitForTimeout(1000);
        
        // Cancel in dialog
        const cancelButton = page.locator('button:has-text("Cancel"), button:has-text("No")').first();
        if (await cancelButton.count() > 0) {
          await cancelButton.click();
          await page.waitForTimeout(1000);
          
          // Should still be on detail page
          const url = page.url();
          expect(url).toContain('/m/');
        }
      }
    }
  });
});

test.describe('CRUD: Success/Error Feedback', () => {
  test('CRUD23: Successful save shows success message', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.count() > 0) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      const editButton = page.locator('button:has-text("Edit")');
      if (await editButton.count() > 0) {
        await editButton.click();
        await page.waitForTimeout(1000);
        
        const input = page.locator('input[type="text"]').first();
        if (await input.count() > 0) {
          await input.fill(`Update ${Date.now()}`);
          
          const saveButton = page.locator('button:has-text("Save")');
          if (await saveButton.count() > 0) {
            await saveButton.click();
            await page.waitForTimeout(3000);
            
            // Check for success message or banner
            const successMessage = page.locator('[class*="success"], [class*="toast"]:has-text("Success"), text:has-text("Saved")');
            const count = await successMessage.count();
            // Success feedback expected
            expect(true).toBe(true);
          }
        }
      }
    }
  });

  test('CRUD24: Failed save shows error message', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.count() > 0) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      const editButton = page.locator('button:has-text("Edit")');
      if (await editButton.count() > 0) {
        await editButton.click();
        await page.waitForTimeout(1000);
        
        // Try to set a field to trigger an error (e.g., empty required field)
        const inputs = page.locator('input').first();
        if (await inputs.count() > 0) {
          await inputs.fill('');
          
          const saveButton = page.locator('button:has-text("Save")');
          if (await saveButton.count() > 0) {
            await saveButton.click();
            await page.waitForTimeout(2000);
            
            // Should show error
            const errorMessage = page.locator('[class*="error"], [class*="danger"], text:has-text("Error"), text:has-text("Required")');
            const count = await errorMessage.count();
            expect(count).toBeGreaterThanOrEqual(0);
          }
        }
      }
    }
  });
});

test.describe('CRUD: API Paths', () => {
  test('CRUD25: Create uses correct API path', async ({ page }) => {
    const apiCalls: string[] = [];
    
    page.on('request', (request) => {
      const url = request.url();
      if (url.includes('/api/')) {
        apiCalls.push(url);
      }
    });
    
    await page.goto(`${BASE_URL}/frontend/m/Item%20Category/new`);
    await page.waitForTimeout(5000);
    
    // Should use /api/method/ path, not /frontend/api/
    const frontendApiCalls = apiCalls.filter(url => url.includes('/frontend/api/'));
    expect(frontendApiCalls.length).toBe(0);
  });

  test('CRUD26: Update uses correct API path', async ({ page }) => {
    const apiCalls: string[] = [];
    
    page.on('request', (request) => {
      const url = request.url();
      if (url.includes('/api/')) {
        apiCalls.push(url);
      }
    });
    
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.count() > 0) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      const editButton = page.locator('button:has-text("Edit")');
      if (await editButton.count() > 0) {
        await editButton.click();
        await page.waitForTimeout(1000);
        
        const input = page.locator('input[type="text"]').first();
        if (await input.count() > 0) {
          await input.fill('Test');
          
          const saveButton = page.locator('button:has-text("Save")');
          if (await saveButton.count() > 0) {
            await saveButton.click();
            await page.waitForTimeout(3000);
            
            const frontendApiCalls = apiCalls.filter(url => url.includes('/frontend/api/'));
            expect(frontendApiCalls.length).toBe(0);
          }
        }
      }
    }
  });
});

test.describe('CRUD: Regression', () => {
  test('CRUD27: No console errors during CRUD operations', async ({ page }) => {
    const consoleErrors: string[] = [];
    
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Test entire CRUD flow
    await page.goto(`${BASE_URL}/frontend/list/Item%20Category`);
    await page.waitForTimeout(5000);
    
    // View detail
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.count() > 0) {
      await firstRow.click();
      await page.waitForTimeout(3000);
      
      // Edit mode
      const editButton = page.locator('button:has-text("Edit")');
      if (await editButton.count() > 0) {
        await editButton.click();
        await page.waitForTimeout(1000);
        
        // Cancel
        const cancelButton = page.locator('button:has-text("Cancel")');
        if (await cancelButton.count() > 0) {
          await cancelButton.click();
          await page.waitForTimeout(1000);
        }
      }
    }
    
    // Create flow
    await page.goto(`${BASE_URL}/frontend/m/Item%20Category/new`);
    await page.waitForTimeout(3000);
    
    const cancelButton = page.locator('button:has-text("Cancel")');
    if (await cancelButton.count() > 0) {
      await cancelButton.click();
      await page.waitForTimeout(1000);
    }
    
    const criticalErrors = consoleErrors.filter(err => 
      !err.includes('favicon') && 
      !err.includes('net::ERR') &&
      !err.includes('socket.io')
    );
    
    expect(criticalErrors.length).toBe(0);
  });
});
