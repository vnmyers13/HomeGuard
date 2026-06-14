import { test, expect } from '@playwright/test';

test.describe('Settings', () => {
  test('settings page loads', async ({ page }) => {
    await page.goto('/settings');
    await expect(page).toHaveURL(/settings/);
  });

  test('shows settings tabs', async ({ page }) => {
    await page.goto('/settings');
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
  });

  test('notification tab is active by default', async ({ page }) => {
    await page.goto('/settings');
    await expect(page.getByRole('heading', { name: 'Notification Preferences' })).toBeVisible();
  });

  test('can switch to account tab', async ({ page }) => {
    await page.goto('/settings');
    await page.getByRole('button', { name: 'Account' }).click();
    await expect(page.getByRole('heading', { name: 'Account Settings' })).toBeVisible();
  });

  test('can switch to data retention tab', async ({ page }) => {
    await page.goto('/settings');
    await page.getByRole('button', { name: 'Data Retention' }).click();
    await expect(page.getByRole('heading', { name: 'Data Retention' })).toBeVisible();
  });

  test('save button is present', async ({ page }) => {
    await page.goto('/settings');
    await expect(page.getByRole('button', { name: /save settings/i })).toBeVisible();
  });
});
