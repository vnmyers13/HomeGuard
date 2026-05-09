"""Screenshot utilities for the Playwright Executor Service."""

import logging
from typing import Optional

from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def capture_screenshot(page: Page, name: str = "screenshot", full_page: bool = False) -> Optional[bytes]:
    """Capture a screenshot of the current page.

    Args:
        page: The Playwright page instance.
        name: Identifier for logging.
        full_page: If True, capture the full scrollable page.

    Returns:
        PNG bytes of the screenshot, or None on failure.
    """
    try:
        png_bytes = await page.screenshot(full_page=full_page)
        logger.debug("Captured screenshot '%s' (%d bytes)", name, len(png_bytes))
        return png_bytes
    except Exception as e:
        logger.warning("Failed to capture screenshot '%s': %s", name, e)
        return None