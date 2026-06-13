"""Action handlers for the 16 playbook action types."""

import asyncio
import json
import logging
from enum import Enum
from typing import Any, Optional

from playwright.async_api import Page

from gw_playwright.screenshot import capture_screenshot
from gw_playwright.token_resolver import resolve_tokens

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    NAVIGATE = "navigate"
    WAIT_SELECTOR = "wait_for_selector"
    CLICK = "click"
    FILL = "fill"
    FILL_AND_PRESS = "fill_and_press"
    SELECT_OPTION = "select_option"
    CHECK = "check"
    UNCHECK = "uncheck"
    SCROLL_DOWN = "scroll_down"
    SCROLL_UP = "scroll_up"
    SCREENSHOT = "screenshot"
    EXTRACT = "extract"
    ASSERT_TEXT = "assert_text"
    ASSERT_URL = "assert_url"
    EXECUTE_JS = "execute_js"
    CUSTOM_EXTRACT = "custom_extract"


class ActionResult:
    """Result of executing a single action."""

    def __init__(self, action_type: str, success: bool, data: Optional[dict] = None, error: Optional[str] = None):
        self.action_type = action_type
        self.success = success
        self.data = data or {}
        self.error = error

    def to_dict(self) -> dict:
        result = {"action": self.action_type, "success": self.success, "data": self.data}
        if self.error:
            result["error"] = self.error
        return result


# --- Individual Action Handlers ---

async def action_navigate(page: Page, params: dict, context: dict) -> ActionResult:
    url = resolve_tokens(params.get("url", ""), context)
    timeout = params.get("timeout", 30000)
    try:
        await page.goto(url, timeout=timeout)
        return ActionResult(ActionType.NAVIGATE, True, {"url": page.url})
    except Exception as e:
        return ActionResult(ActionType.NAVIGATE, False, error=str(e))


async def action_wait_for_selector(page: Page, params: dict, context: dict) -> ActionResult:
    selector = resolve_tokens(params.get("selector", ""), context)
    timeout = params.get("timeout", 10000)
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        return ActionResult(ActionType.WAIT_SELECTOR, True)
    except Exception as e:
        return ActionResult(ActionType.WAIT_SELECTOR, False, error=str(e))


async def action_click(page: Page, params: dict, context: dict) -> ActionResult:
    selector = resolve_tokens(params.get("selector", ""), context)
    try:
        await page.click(selector)
        return ActionResult(ActionType.CLICK, True)
    except Exception as e:
        return ActionResult(ActionType.CLICK, False, error=str(e))


async def action_fill(page: Page, params: dict, context: dict) -> ActionResult:
    selector = resolve_tokens(params.get("selector", ""), context)
    value = resolve_tokens(params.get("value", ""), context)
    try:
        await page.fill(selector, value)
        return ActionResult(ActionType.FILL, True)
    except Exception as e:
        return ActionResult(ActionType.FILL, False, error=str(e))


async def action_fill_and_press(page: Page, params: dict, context: dict) -> ActionResult:
    selector = resolve_tokens(params.get("selector", ""), context)
    value = resolve_tokens(params.get("value", ""), context)
    key = params.get("key", "Enter")
    try:
        await page.fill(selector, value)
        await page.press(selector, key)
        return ActionResult(ActionType.FILL_AND_PRESS, True)
    except Exception as e:
        return ActionResult(ActionType.FILL_AND_PRESS, False, error=str(e))


async def action_select_option(page: Page, params: dict, context: dict) -> ActionResult:
    selector = resolve_tokens(params.get("selector", ""), context)
    value = resolve_tokens(params.get("value", ""), context)
    try:
        await page.select_option(selector, value)
        return ActionResult(ActionType.SELECT_OPTION, True)
    except Exception as e:
        return ActionResult(ActionType.SELECT_OPTION, False, error=str(e))


async def action_check(page: Page, params: dict, context: dict) -> ActionResult:
    selector = resolve_tokens(params.get("selector", ""), context)
    try:
        await page.check(selector)
        return ActionResult(ActionType.CHECK, True)
    except Exception as e:
        return ActionResult(ActionType.CHECK, False, error=str(e))


async def action_uncheck(page: Page, params: dict, context: dict) -> ActionResult:
    selector = resolve_tokens(params.get("selector", ""), context)
    try:
        await page.uncheck(selector)
        return ActionResult(ActionType.UNCHECK, True)
    except Exception as e:
        return ActionResult(ActionType.UNCHECK, False, error=str(e))


async def action_scroll_down(page: Page, params: dict, context: dict) -> ActionResult:
    pixels = params.get("pixels", 500)
    try:
        await page.evaluate(f"window.scrollBy(0, {pixels})")
        return ActionResult(ActionType.SCROLL_DOWN, True)
    except Exception as e:
        return ActionResult(ActionType.SCROLL_DOWN, False, error=str(e))


async def action_scroll_up(page: Page, params: dict, context: dict) -> ActionResult:
    pixels = params.get("pixels", 500)
    try:
        await page.evaluate(f"window.scrollBy(0, -{pixels})")
        return ActionResult(ActionType.SCROLL_UP, True)
    except Exception as e:
        return ActionResult(ActionType.SCROLL_UP, False, error=str(e))


async def action_screenshot(page: Page, params: dict, context: dict) -> ActionResult:
    name = params.get("name", "step")
    full_page = params.get("full_page", True)
    try:
        png_bytes = await capture_screenshot(page, name=name, full_page=full_page)
        return ActionResult(ActionType.SCREENSHOT, True, {"size": len(png_bytes), "name": name})
    except Exception as e:
        return ActionResult(ActionType.SCREENSHOT, False, error=str(e))


async def action_extract(page: Page, params: dict, context: dict) -> ActionResult:
    """Extract data from selectors."""
    extractions = params.get("extractions", [])  # list of {selector, attribute?, key}
    data = {}
    errors = []

    for ext in extractions:
        selector = resolve_tokens(ext.get("selector", ""), context)
        key = ext.get("key", "data")
        attribute = ext.get("attribute")

        try:
            if attribute:
                value = await page.evaluate(
                    f"document.querySelector('{selector}')?.getAttribute('{attribute}') || ''"
                )
            else:
                value = await page.inner_text(selector)

            data[key] = value.strip() if isinstance(value, str) else value
        except Exception as e:
            errors.append(f"{key}: {e}")

    success = len(errors) == 0
    return ActionResult(ActionType.EXTRACT, success, data=data, error="; ".join(errors) if errors else None)


async def action_assert_text(page: Page, params: dict, context: dict) -> ActionResult:
    selector = resolve_tokens(params.get("selector", ""), context)
    expected = resolve_tokens(params.get("expected", ""), context)
    contains = params.get("contains", True)

    try:
        text = await page.inner_text(selector)
        if contains:
            passed = expected in text
        else:
            passed = text.strip() == expected

        return ActionResult(
            ActionType.ASSERT_TEXT,
            passed,
            data={"actual": text.strip(), "expected": expected, "contains": contains},
            error="Assertion failed" if not passed else None,
        )
    except Exception as e:
        return ActionResult(ActionType.ASSERT_TEXT, False, error=str(e))


async def action_assert_url(page: Page, params: dict, context: dict) -> ActionResult:
    expected = resolve_tokens(params.get("expected", ""), context)
    contains = params.get("contains", True)

    try:
        current_url = page.url
        if contains:
            passed = expected in current_url
        else:
            passed = current_url == expected

        return ActionResult(
            ActionType.ASSERT_URL,
            passed,
            data={"actual": current_url, "expected": expected},
            error="URL assertion failed" if not passed else None,
        )
    except Exception as e:
        return ActionResult(ActionType.ASSERT_URL, False, error=str(e))


async def action_execute_js(page: Page, params: dict, context: dict) -> ActionResult:
    script = resolve_tokens(params.get("script", ""), context)
    try:
        result = await page.evaluate(script)
        return ActionResult(ActionType.EXECUTE_JS, True, data={"result": result})
    except Exception as e:
        return ActionResult(ActionType.EXECUTE_JS, False, error=str(e))


async def action_custom_extract(page: Page, params: dict, context: dict) -> ActionResult:
    """Run a custom JavaScript extraction and return structured data."""
    script = resolve_tokens(params.get("script", ""), context)
    try:
        result = await page.evaluate(script)
        # Ensure result is JSON serializable
        if result is None:
            result = {}
        data = json.loads(json.dumps(result)) if not isinstance(result, dict) else result
        return ActionResult(ActionType.CUSTOM_EXTRACT, True, data=data)
    except Exception as e:
        return ActionResult(ActionType.CUSTOM_EXTRACT, False, error=str(e))


# --- Handler Registry ---
HANDLERS = {
    ActionType.NAVIGATE: action_navigate,
    ActionType.WAIT_SELECTOR: action_wait_for_selector,
    ActionType.CLICK: action_click,
    ActionType.FILL: action_fill,
    ActionType.FILL_AND_PRESS: action_fill_and_press,
    ActionType.SELECT_OPTION: action_select_option,
    ActionType.CHECK: action_check,
    ActionType.UNCHECK: action_uncheck,
    ActionType.SCROLL_DOWN: action_scroll_down,
    ActionType.SCROLL_UP: action_scroll_up,
    ActionType.SCREENSHOT: action_screenshot,
    ActionType.EXTRACT: action_extract,
    ActionType.ASSERT_TEXT: action_assert_text,
    ActionType.ASSERT_URL: action_assert_url,
    ActionType.EXECUTE_JS: action_execute_js,
    ActionType.CUSTOM_EXTRACT: action_custom_extract,
}


async def execute_action(page: Page, action_type: str, params: dict, context: dict) -> ActionResult:
    """Dispatch and execute a single action by type."""
    handler = HANDLERS.get(action_type)
    if handler is None:
        return ActionResult(action_type, False, error=f"Unknown action type: {action_type}")

    try:
        result = await handler(page, params, context)
        return result
    except Exception as e:
        logger.error("Action %s failed unexpectedly: %s", action_type, e)
        return ActionResult(action_type, False, error=str(e))


async def execute_actions(page: Page, actions: list[dict], context: dict) -> list[ActionResult]:
    """Execute a sequence of actions, stopping on fatal error."""
    results = []
    for i, action in enumerate(actions):
        action_type = action.get("type", "")
        params = action.get("params", {})

        result = await execute_action(page, action_type, params, context)
        results.append(result)

        # Stop on assertion failures or unknown actions
        if not result.success and action_type in (ActionType.ASSERT_TEXT, ActionType.ASSERT_URL):
            logger.warning("Assertion failed at step %d; stopping execution.", i)
            break

        # Small delay between actions for stability
        if result.success and action_type not in (ActionType.WAIT_SELECTOR,):
            await asyncio.sleep(0.1)

    return results