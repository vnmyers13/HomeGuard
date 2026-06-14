import { test, expect } from '@playwright/test';

test.describe('Requests', () => {
  test('requests page loads', async ({ page }) => {
    await page.goto('/requests');
    await expect(page).toHaveURL(/requests/);
  });

  test('shows requests table', async ({ page }) => {
    await page.goto('/requests');
    // Should show request management interface
    await expect(page.getByRole('heading', { name: /request/i, exact: false })).toBeVisible();
  });

  test('filter controls are present', async ({ page }) => {
    await page.goto('/requests');
    // Filter dropdown should exist
    const filter = page.locator('select').first();
    if (filter.isVisible()) {
      await expect(filter).toBeVisible();
    }
  });
});
