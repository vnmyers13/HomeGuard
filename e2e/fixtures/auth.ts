import { test as base, expect } from '@playwright/test';

/**
 * Auth fixture - logs in a test user before each test.
 */
export const test = base.extend({
  loggedInPage: async ({ page }, use) => {
    // Navigate to login
    await page.goto('/login');

    // Fill credentials
    await page.getByLabel('Email or username').fill('test@example.com');
    await page.getByLabel('Password').fill('Testpassword1!');

    // Submit
    await page.getByRole('button', { name: /sign in|login/i }).click();

    // Wait for redirect
    await page.waitForURL(/^(?!.*login).*$/, { timeout: 10000 });

    await use(page);
  },
});

export { expect };
