import { test as base } from '@playwright/test';

/**
 * Navigation fixture - provides helper functions for common navigation actions.
 */
export const test = base.extend({
  navigateToOverview: async ({ page }, use) => {
    await page.goto('/');
    await expect(page).toHaveURL('/');
    await use(page);
  },

  navigateToProfiles: async ({ page }, use) => {
    await page.goto('/profile');
    await expect(page).toHaveURL('/profile');
    await use(page);
  },

  navigateToScans: async ({ page }, use) => {
    await page.goto('/scans');
    await expect(page).toHaveURL('/scans');
    await use(page);
  },

  navigateToRequests: async ({ page }, use) => {
    await page.goto('/requests');
    await expect(page).toHaveURL('/requests');
    await use(page);
  },

  navigateToSettings: async ({ page }, use) => {
    await page.goto('/settings');
    await expect(page).toHaveURL('/settings');
    await use(page);
  },

  navigateToReports: async ({ page }, use) => {
    await page.goto('/reports');
    await expect(page).toHaveURL('/reports');
    await use(page);
  },
});

export { test };
