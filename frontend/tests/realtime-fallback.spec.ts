import { test, expect } from '@playwright/test'

const BASE_URL = process.env.TEST_BASE_URL || 'http://test.localhost:8002'

test.describe('Realtime Fallback Tests', () => {
  test.describe.configure({ mode: 'serial' })
  
  test.beforeEach(async ({ page }) => {
    const consoleErrors: string[] = []
    const socketErrors: string[] = []
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text()
        consoleErrors.push(text)
        if (text.includes('socket') || text.includes('Socket') || text.includes('ERR_CONNECTION_REFUSED')) {
          socketErrors.push(text)
        }
      }
    })
    
    await page.context().storageState({ path: 'auth-state.json' })
  })
  
  test('Test RF1: Recovery page loads without socket connection errors', async ({ page }) => {
    const consoleErrors: string[] = []
    const socketConnectionErrors: string[] = []
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text()
        consoleErrors.push(text)
        if (
          text.includes('socket') || 
          text.includes('Socket') || 
          text.includes('ERR_CONNECTION_REFUSED') ||
          text.includes('9000')
        ) {
          socketConnectionErrors.push(text)
        }
      }
    })
    
    await page.goto(`${BASE_URL}/frontend/recovery`)
    await page.waitForTimeout(3000)
    
    expect(consoleErrors.filter(e => e.includes('Invalid URL') || e.includes('/frontend/api'))).toHaveLength(0)
    
    expect(socketConnectionErrors.filter(e => e.includes('ERR_CONNECTION_REFUSED'))).toHaveLength(0)
  })
  
  test('Test RF2: Recovery detail page loads without socket connection errors', async ({ page }) => {
    const consoleErrors: string[] = []
    const socketConnectionErrors: string[] = []
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text()
        consoleErrors.push(text)
        if (
          text.includes('socket') || 
          text.includes('Socket') || 
          text.includes('ERR_CONNECTION_REFUSED') ||
          text.includes('9000')
        ) {
          socketConnectionErrors.push(text)
        }
      }
    })
    
    await page.goto(`${BASE_URL}/frontend/recovery`)
    await page.waitForTimeout(3000)
    
    const recoveryLink = page.locator('a[href*="/recovery/"], button:has-text("Recovery")').first()
    if (await recoveryLink.count() > 0) {
      await recoveryLink.click()
      await page.waitForTimeout(3000)
    }
    
    expect(consoleErrors.filter(e => e.includes('Invalid URL'))).toHaveLength(0)
    expect(socketConnectionErrors.filter(e => e.includes('ERR_CONNECTION_REFUSED'))).toHaveLength(0)
  })
  
  test('Test RF3: No blocking error screen on recovery pages', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/recovery`)
    await page.waitForTimeout(3000)
    
    const bodyText = await page.textContent('body')
    
    const hasBlockingError = 
      bodyText?.includes('Connection Error') ||
      bodyText?.includes('Socket Error') ||
      bodyText?.includes('Unable to connect')
    
    expect(hasBlockingError).not.toBeTruthy()
  })
  
  test('Test RF4: Recovery page renders case list via API', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/recovery`)
    await page.waitForTimeout(5000)
    
    const pageContent = await page.content()
    
    const hasRecoveryContent = 
      pageContent.includes('Recovery') ||
      pageContent.includes('Case') ||
      pageContent.includes('Finder')
    
    expect(hasRecoveryContent).toBeTruthy()
  })
  
  test('Test RF5: No /frontend/api calls (wrong API path)', async ({ page }) => {
    const apiCalls: string[] = []
    
    page.on('request', request => {
      if (request.url().includes('/frontend/api')) {
        apiCalls.push(request.url())
      }
    })
    
    await page.goto(`${BASE_URL}/frontend/recovery`)
    await page.waitForTimeout(3000)
    
    expect(apiCalls).toHaveLength(0)
  })
  
  test('Test RF6: Console does not spam repeated socket errors', async ({ page }) => {
    const socketErrors: string[] = []
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text()
        if (
          text.includes('socket') || 
          text.includes('Socket') || 
          text.includes('ERR_CONNECTION_REFUSED') ||
          text.includes('connection')
        ) {
          socketErrors.push(text)
        }
      }
    })
    
    await page.goto(`${BASE_URL}/frontend/recovery`)
    
    await page.waitForTimeout(10000)
    
    const uniqueErrors = new Set(socketErrors)
    expect(uniqueErrors.size).toBeLessThanOrEqual(2)
  })
})

test.describe('Realtime Fallback - Navigation Tests', () => {
  test('Test N1: Frontend to recovery navigation works', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend`)
    await page.waitForTimeout(3000)
    
    await page.goto(`${BASE_URL}/frontend/recovery`)
    await page.waitForTimeout(3000)
    
    expect(page.url()).toContain('/frontend/recovery')
  })
  
  test('Test N2: Recovery to detail navigation works', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend/recovery`)
    await page.waitForTimeout(3000)
    
    const caseLink = page.locator('button:has-text("Recovery -"), a:has-text("Recovery -")').first()
    
    if (await caseLink.count() > 0) {
      await caseLink.click()
      await page.waitForTimeout(3000)
      
      expect(page.url()).toMatch(/\/frontend\/recovery\/[^/]+/)
    }
  })
  
  test('Test N3: No dashboard route - stays under /frontend', async ({ page }) => {
    await page.goto(`${BASE_URL}/frontend`)
    await page.waitForTimeout(3000)
    
    expect(page.url()).toContain('/frontend')
    expect(page.url()).not.toContain('/dashboard')
  })
})

test.describe('Realtime Fallback - API Validation', () => {
  test('Test API1: Recovery APIs work without realtime', async ({ request }) => {
    const recoveryResponse = await request.post(`${BASE_URL}/api/method/scanifyme.recovery.api.recovery_api.get_owner_recovery_cases`, {
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    expect(recoveryResponse.status()).toBe(200)
    
    const json = await recoveryResponse.json()
    expect(json.message).toBeDefined()
  })
  
  test('Test API2: No CSRF failures on recovery API', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/api/method/scanifyme.recovery.api.recovery_api.get_owner_recovery_cases`, {
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    expect(response.status()).toBe(200)
  })
})
