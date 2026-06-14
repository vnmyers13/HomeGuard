import { test, expect } from '@playwright/test';

test.describe('Scans', () => {
  test('scans page loads', async ({ page }) => {
    await page.goto('/scans');
    await expect(page).toHaveURL(/scans/);
  });

  test('shows scans list', async ({ page }) => {
    await page.goto('/scans');
    await expect(page.getByRole('heading', { name: /scan/i, exact: false })).toBeVisible();
  });

  test('trigger scan button is present', async ({ page }) => {
    await page.goto('/scans');
    const triggerBtn = page.getByRole('button', { name: /trigger|start|new scan/i });
    if (triggerBtn.isVisible()) {
      await expect(triggerBtn).toBeVisible();
    }
  });
});
