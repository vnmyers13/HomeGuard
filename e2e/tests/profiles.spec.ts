import { test, expect } from '@playwright/test';

test.describe('Profiles', () => {
  test('profile page loads', async ({ page }) => {
    await page.goto('/profile');
    await expect(page).toHaveURL(/profile/);
  });

  test('shows profile form', async ({ page }) => {
    await page.goto('/profile');
    // Should show profile management interface
    await expect(page.getByRole('heading', { name: /profile/i, exact: false })).toBeVisible();
  });

  test('can fill profile form fields', async ({ page }) => {
    await page.goto('/profile');
    const nameInput = page.getByRole('textbox', { name: /name/i }).first();
    if (nameInput.isVisible()) {
      await nameInput.fill('Test Profile');
      await expect(nameInput).toHaveValue('Test Profile');
    }
  });
});
