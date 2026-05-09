"""Browser pool with anti-detection configuration."""

import asyncio
import json
import logging
import os
import random
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, BrowserContext, Playwright

logger = logging.getLogger(__name__)

# Weighted user-agent selection
_USER_AGENTS_PATH = Path(__file__).parent / "user_agents.json"


def _load_user_agents() -> list[dict]:
    """Load user agent profiles from JSON."""
    with open(_USER_AGENTS_PATH, "r") as f:
        return json.load(f)


def _pick_user_agent() -> dict:
    """Pick a user agent using weighted random selection, falling back to uniform."""
    agents = _load_user_agents()
    # Build weighted pool: each agent appears `weight` times
    pool = []
    for entry in agents:
        weight = max(entry.get("weight", 1), 0)
        pool.extend([entry] * weight)

    if not pool:
        # All weights zero → uniform random
        pool = agents
    return random.choice(pool)


class BrowserPool:
    """Manages a pool of Playwright browser contexts with anti-detection settings."""

    def __init__(self, max_concurrent: int = 3):
        self._max_concurrent = max_concurrent
        self._playwright: Optional[Playwright] = None
        self._contexts: list[BrowserContext] = []
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._lock = asyncio.Lock()
        self._initialized = False

    @property
    def pool_size(self) -> int:
        return self._max_concurrent

    @property
    def available(self) -> int:
        return self._semaphore._value

    @property
    def busy(self) -> int:
        return self._max_concurrent - self._semaphore._value

    async def initialize(self):
        """Start Playwright and pre-warm browser contexts."""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            logger.info("Initializing browser pool (max=%d)...", self._max_concurrent)
            pw = await async_playwright().start()
            self._playwright = pw

            # Pre-warm contexts
            for _ in range(self._max_concurrent):
                ctx = await self._create_context()
                self._contexts.append(ctx)

            self._initialized = True
            logger.info("Browser pool initialized with %d contexts.", len(self._contexts))

    async def _create_context(self) -> BrowserContext:
        """Create a single browser context with anti-detection settings."""
        agent = _pick_user_agent()
        ua_string = agent["ua"]

        browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--window-size=1920,1080",
            ],
        )

        ctx = await browser.new_context(
            user_agent=ua_string,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
            java_script_enabled=True,
            bypass_csp=False,
        )

        # Stealth: override navigator.webdriver
        await ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            // Override plugins to look like a real browser
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            // Override languages
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """)

        return ctx

    async def acquire(self) -> BrowserContext:
        """Acquire a browser context from the pool. Blocks if none available."""
        await self._semaphore.acquire()
        async with self._lock:
            # Pop a context; if none available, create a new one (overflow)
            if self._contexts:
                ctx = self._contexts.pop()
            else:
                ctx = await self._create_context()
        return ctx

    async def release(self, context: BrowserContext):
        """Release a browser context back to the pool."""
        async with self._lock:
            if len(self._contexts) < self._max_concurrent:
                # Reuse the context
                self._contexts.append(context)
            else:
                # Pool is full, close the overflow context
                try:
                    await context.close()
                except Exception:
                    pass
        self._semaphore.release()

    async def close(self):
        """Shut down the pool and all contexts."""
        async with self._lock:
            for ctx in self._contexts:
                try:
                    await ctx.close()
                except Exception:
                    pass
            self._contexts.clear()

            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

            self._initialized = False
            logger.info("Browser pool shut down.")


# Singleton instance
_pool: Optional[BrowserPool] = None


async def get_pool() -> BrowserPool:
    """Get or create the global browser pool singleton."""
    global _pool
    if _pool is None:
        max_concurrent = int(os.getenv("PLAYWRIGHT_POOL_SIZE", "3"))
        _pool = BrowserPool(max_concurrent=max_concurrent)
        await _pool.initialize()
    return _pool


async def shutdown_pool():
    """Shut down the global browser pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None