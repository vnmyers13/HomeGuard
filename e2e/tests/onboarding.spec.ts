import { test, expect } from '@playwright/test';

test.describe('Onboarding Wizard', () => {
  test('shows onboarding step 0 (welcome)', async ({ page }) => {
    await page.goto('/onboarding');
    await expect(page.getByText('Welcome to HomeGuard')).toBeVisible();
    await expect(page.getByText('Get started with HomeGuard')).toBeVisible();
  });

  test('navigates through onboarding steps', async ({ page }) => {
    await page.goto('/onboarding');

    // Step 0: Welcome -> Continue
    await page.getByRole('button', { name: /continue|get started/i }).click();
    await expect(page.getByText('Create Your Household')).toBeVisible();

    // Step 1: Household -> Continue
    await page.getByRole('textbox', { name: /household name/i }).fill('Test Household');
    await page.getByRole('button', { name: /continue/i }).click();
    await expect(page.getByText('Add Your First Profile')).toBeVisible();

    // Step 2: Profile -> Continue
    await page.getByRole('textbox', { name: /name/i }).first().fill('Test User');
    await page.getByRole('button', { name: /continue/i }).click();
    await expect(page.getByText('Connect Your Email')).toBeVisible();

    // Step 3: Email -> Continue
    await page.getByRole('button', { name: /continue/i }).click();
    await expect(page.getByText('Ready for Your First Scan')).toBeVisible();
  });

  test('can skip after step 2', async ({ page }) => {
    await page.goto('/onboarding');

    // Navigate to step 2
    await page.getByRole('button', { name: /continue|get started/i }).click();
    await page.getByRole('textbox', { name: /household name/i }).fill('Test');
    await page.getByRole('button', { name: /continue/i }).click();

    // Skip button should appear
    await expect(page.getByRole('button', { name: /skip/i })).toBeVisible();
  });

  test('back button works', async ({ page }) => {
    await page.goto('/onboarding');
    await page.getByRole('button', { name: /continue|get started/i }).click();

    // Should be on step 1
    await expect(page.getByText('Create Your Household')).toBeVisible();

    // Go back
    await page.getByRole('button', { name: /back/i }).click();

    // Should be back on step 0
    await expect(page.getByText('Welcome to HomeGuard')).toBeVisible();
  });

  test('shows validation error for empty household name', async ({ page }) => {
    await page.goto('/onboarding');
    await page.getByRole('button', { name: /continue|get started/i }).click();

    // Try to continue without household name
    await page.getByRole('button', { name: /continue/i }).click();

    // Should show error
    await expect(page.getByText(/Please enter a household name/i)).toBeVisible();
  });
});
