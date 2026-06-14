import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('overview page loads', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL('/');
  });

  test('shows dashboard header', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /dashboard|overview/i })).toBeVisible();
  });

  test('sidebar is visible', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('nav').first()).toBeVisible();
  });

  test('navigation links are present', async ({ page }) => {
    await page.goto('/');
    const navItems = ['Overview', 'My Profile', 'Household', 'Brokers', 'Scans', 'Requests', 'Reports', 'Notifications', 'System Health'];
    for (const item of navItems) {
      await expect(page.getByRole('link', { name: item }).first()).toBeVisible();
    }
  });

  test('settings link navigates to settings page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'Settings' }).first().click();
    await expect(page).toHaveURL(/settings/);
  });

  test('reports link navigates to reports page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'Reports' }).first().click();
    await expect(page).toHaveURL(/reports/);
  });

  test('health link navigates to health page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'System Health' }).first().click();
    await expect(page).toHaveURL(/health/);
  });
});
