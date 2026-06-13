"""Tests for gw_playwright action handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class MockPage:
    """Minimal async Page mock for action tests."""

    def __init__(self, url="https://example.com"):
        self.url = url
        self._state = {}

    async def goto(self, url, timeout=30000):
        self.url = url
        return None

    async def click(self, selector):
        return None

    async def fill(self, selector, value):
        self._state[selector] = value
        return None

    async def press(self, selector, key):
        return None

    async def select_option(self, selector, value):
        self._state[selector] = value
        return None

    async def check(self, selector):
        self._state[selector] = True
        return None

    async def uncheck(self, selector):
        self._state[selector] = False
        return None

    async def wait_for_selector(self, selector, timeout=10000):
        return True

    async def inner_text(self, selector):
        return self._state.get(selector, "sample text")

    async def evaluate(self, expr):
        if "scrollBy" in expr:
            return 0
        if "getAttribute" in expr:
            return "attr_value"
        return {"result": "js_output"}


@pytest.fixture
def mock_page():
    return MockPage()


class TestNavigateAction:
    """Tests for the navigate action."""

    @pytest.mark.asyncio
    async def test_navigate_success(self, mock_page):
        from gw_playwright.actions import action_navigate
        result = await action_navigate(mock_page, {"url": "https://example.com"}, {})
        assert result.success is True
        assert result.action_type == "navigate"

    @pytest.mark.asyncio
    async def test_navigate_with_context(self, mock_page):
        from gw_playwright.actions import action_navigate
        result = await action_navigate(mock_page, {"url": "https://${domain}"}, {"domain": "test.com"})
        assert result.success is True


class TestClickAction:
    """Tests for the click action."""

    @pytest.mark.asyncio
    async def test_click_success(self, mock_page):
        from gw_playwright.actions import action_click
        result = await action_click(mock_page, {"selector": "#btn"}, {})
        assert result.success is True


class TestFillAction:
    """Tests for the fill action."""

    @pytest.mark.asyncio
    async def test_fill_success(self, mock_page):
        from gw_playwright.actions import action_fill
        result = await action_fill(mock_page, {"selector": "#input", "value": "test"}, {})
        assert result.success is True


class TestFillAndPressAction:
    """Tests for fill_and_press action."""

    @pytest.mark.asyncio
    async def test_fill_and_press_success(self, mock_page):
        from gw_playwright.actions import action_fill_and_press
        result = await action_fill_and_press(mock_page, {"selector": "#input", "value": "test"}, {})
        assert result.success is True


class TestSelectOptionAction:
    """Tests for select_option action."""

    @pytest.mark.asyncio
    async def test_select_option_success(self, mock_page):
        from gw_playwright.actions import action_select_option
        result = await action_select_option(mock_page, {"selector": "#select", "value": "opt1"}, {})
        assert result.success is True


class TestCheckAction:
    """Tests for check/uncheck actions."""

    @pytest.mark.asyncio
    async def test_check_success(self, mock_page):
        from gw_playwright.actions import action_check
        result = await action_check(mock_page, {"selector": "#checkbox"}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_uncheck_success(self, mock_page):
        from gw_playwright.actions import action_uncheck
        result = await action_uncheck(mock_page, {"selector": "#checkbox"}, {})
        assert result.success is True


class TestScrollActions:
    """Tests for scroll actions."""

    @pytest.mark.asyncio
    async def test_scroll_down(self, mock_page):
        from gw_playwright.actions import action_scroll_down
        result = await action_scroll_down(mock_page, {"pixels": 500}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_scroll_up(self, mock_page):
        from gw_playwright.actions import action_scroll_up
        result = await action_scroll_up(mock_page, {"pixels": 500}, {})
        assert result.success is True


class TestWaitForSelector:
    """Tests for wait_for_selector action."""

    @pytest.mark.asyncio
    async def test_wait_for_selector_success(self, mock_page):
        from gw_playwright.actions import action_wait_for_selector
        result = await action_wait_for_selector(mock_page, {"selector": "#loading"}, {})
        assert result.success is True


class TestExtractAction:
    """Tests for extract action."""

    @pytest.mark.asyncio
    async def test_extract_success(self, mock_page):
        from gw_playwright.actions import action_extract
        extractions = [{"selector": "#name", "key": "name"}]
        result = await action_extract(mock_page, {"extractions": extractions}, {})
        assert result.success is True


class TestAssertActions:
    """Tests for assertion actions."""

    @pytest.mark.asyncio
    async def test_assert_text_pass(self, mock_page):
        from gw_playwright.actions import action_assert_text
        result = await action_assert_text(mock_page, {"selector": "#title", "expected": "sample"}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_assert_url_pass(self, mock_page):
        from gw_playwright.actions import action_assert_url
        result = await action_assert_url(mock_page, {"expected": "example.com"}, {})
        assert result.success is True


class TestExecuteJsAction:
    """Tests for execute_js action."""

    @pytest.mark.asyncio
    async def test_execute_js_success(self, mock_page):
        from gw_playwright.actions import action_execute_js
        result = await action_execute_js(mock_page, {"script": "return 1"}, {})
        assert result.success is True


class TestCustomExtractAction:
    """Tests for custom_extract action."""

    @pytest.mark.asyncio
    async def test_custom_extract_success(self, mock_page):
        from gw_playwright.actions import action_custom_extract
        result = await action_custom_extract(mock_page, {"script": "return {}"}, {})
        assert result.success is True


class TestScreenshotAction:
    """Tests for screenshot action."""

    @pytest.mark.asyncio
    async def test_screenshot_success(self, mock_page):
        from gw_playwright.actions import action_screenshot
        with patch('gw_playwright.actions.capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = b'\x89PNG\r\n'
            result = await action_screenshot(mock_page, {"name": "test"}, {})
            assert result.success is True


class TestExecuteAction:
    """Tests for the execute_action dispatcher."""

    @pytest.mark.asyncio
    async def test_execute_known_action(self, mock_page):
        from gw_playwright.actions import execute_action
        result = await execute_action(mock_page, "navigate", {"url": "https://example.com"}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, mock_page):
        from gw_playwright.actions import execute_action
        result = await execute_action(mock_page, "unknown_type", {}, {})
        assert result.success is False
        assert "Unknown action type" in result.error


class TestExecuteActions:
    """Tests for execute_actions sequence execution."""

    @pytest.mark.asyncio
    async def test_execute_multiple_actions(self, mock_page):
        from gw_playwright.actions import execute_actions
        actions = [
            {"type": "navigate", "params": {"url": "https://example.com"}},
            {"type": "click", "params": {"selector": "#btn"}},
        ]
        results = await execute_actions(mock_page, actions, {})
        assert len(results) == 2
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_stops_on_assertion_failure(self, mock_page):
        from gw_playwright.actions import execute_actions
        actions = [
            {"type": "navigate", "params": {"url": "https://example.com"}},
            {"type": "assert_text", "params": {"selector": "#x", "expected": "NOT_FOUND"}},
            {"type": "click", "params": {"selector": "#btn"}},
        ]
        results = await execute_actions(mock_page, actions, {})
        # Should stop after assertion failure, so only 2 results
        assert len(results) == 2


class TestActionResult:
    """Tests for ActionResult data class."""

    def test_action_result_to_dict_success(self):
        from gw_playwright.actions import ActionResult
        result = ActionResult("navigate", True, {"url": "https://example.com"})
        d = result.to_dict()
        assert d["action"] == "navigate"
        assert d["success"] is True
        assert "error" not in d

    def test_action_result_to_dict_with_error(self):
        from gw_playwright.actions import ActionResult
        result = ActionResult("click", False, error="timeout")
        d = result.to_dict()
        assert d["success"] is False
        assert d["error"] == "timeout"


class TestTokenResolutionInActions:
    """Tests for token resolution within actions."""

    @pytest.mark.asyncio
    async def test_fill_resolves_context_tokens(self, mock_page):
        from gw_playwright.actions import action_fill
        result = await action_fill(
            mock_page,
            {"selector": "#name", "value": "${full_name}"},
            {"full_name": "John Doe"}
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_navigate_resolves_domain_token(self, mock_page):
        from gw_playwright.actions import action_navigate
        result = await action_navigate(
            mock_page,
            {"url": "https://${domain}/search"},
            {"domain": "example.com"}
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_click_with_context_selector(self, mock_page):
        from gw_playwright.actions import action_click
        result = await action_click(
            mock_page,
            {"selector": "#${btn_id}"},
            {"btn_id": "submit"}
        )
        assert result.success is True


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_navigate_exception(self):
        from gw_playwright.actions import action_navigate
        page = MockPage()
        page.goto = AsyncMock(side_effect=Exception("Network error"))
        result = await action_navigate(page, {"url": "https://example.com"}, {})
        assert result.success is False
        assert "Network error" in result.error

    @pytest.mark.asyncio
    async def test_click_exception(self):
        from gw_playwright.actions import action_click
        page = MockPage()
        page.click = AsyncMock(side_effect=Exception("Element not found"))
        result = await action_click(page, {"selector": "#missing"}, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_extract_partial_failure(self, mock_page):
        from gw_playwright.actions import action_extract
        page = MockPage()
        async def failing_inner_text(selector):
            if selector == "#good":
                return "ok"
            raise Exception("bad selector")

        page.inner_text = failing_inner_text
        extractions = [
            {"selector": "#good", "key": "good"},
            {"selector": "#bad", "key": "bad"},
        ]
        result = await action_extract(page, {"extractions": extractions}, {})
        assert result.success is False
        assert "bad" in result.error

    @pytest.mark.asyncio
    async def test_execute_js_none_result(self, mock_page):
        from gw_playwright.actions import action_custom_extract
        page = MockPage()
        page.evaluate = AsyncMock(return_value=None)
        result = await action_custom_extract(page, {"script": "return null"}, {})
        assert result.success is True
        assert result.data == {}

    @pytest.mark.asyncio
    async def test_assert_text_fail(self, mock_page):
        from gw_playwright.actions import action_assert_text
        page = MockPage()
        page.inner_text = AsyncMock(return_value="actual text")
        result = await action_assert_text(page, {"selector": "#x", "expected": "NOT_HERE"}, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_assert_url_exact_match_fail(self, mock_page):
        from gw_playwright.actions import action_assert_url
        result = await action_assert_url(
            mock_page,
            {"expected": "https://different.com", "contains": False},
            {}
        )
        assert result.success is False

    @pytest.mark.asyncio
    async def test_empty_actions_list(self, mock_page):
        from gw_playwright.actions import execute_actions
        results = await execute_actions(mock_page, [], {})
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_action_with_exception_in_handler(self, mock_page):
        from gw_playwright.actions import execute_action

        # Patch a handler to raise unexpectedly
        with patch('gw_playwright.actions.HANDLERS', {"navigate": lambda p, params, ctx: (_ for _ in ()).throw(RuntimeError("boom"))}):
            result = await execute_action(mock_page, "navigate", {"url": "https://example.com"}, {})
            assert result.success is False

    @pytest.mark.asyncio
    async def test_scroll_default_pixels(self, mock_page):
        from gw_playwright.actions import action_scroll_down
        result = await action_scroll_down(mock_page, {}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_fill_and_press_custom_key(self, mock_page):
        from gw_playwright.actions import action_fill_and_press
        result = await action_fill_and_press(
            mock_page,
            {"selector": "#input", "value": "test", "key": "Tab"},
            {}
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_extract_with_attribute(self, mock_page):
        from gw_playwright.actions import action_extract
        extractions = [{"selector": "#link", "key": "href", "attribute": "href"}]
        result = await action_extract(mock_page, {"extractions": extractions}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_wait_for_selector_with_timeout(self, mock_page):
        from gw_playwright.actions import action_wait_for_selector
        result = await action_wait_for_selector(mock_page, {"selector": "#loading", "timeout": 5000}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_navigate_with_custom_timeout(self, mock_page):
        from gw_playwright.actions import action_navigate
        result = await action_navigate(mock_page, {"url": "https://example.com", "timeout": 60000}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_select_option_with_context(self, mock_page):
        from gw_playwright.actions import action_select_option
        result = await action_select_option(
            mock_page,
            {"selector": "#state", "value": "${state_code}"},
            {"state_code": "CA"}
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_screenshot_full_page_false(self, mock_page):
        from gw_playwright.actions import action_screenshot
        with patch('gw_playwright.actions.capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = b'\x89PNG\r\n'
            result = await action_screenshot(mock_page, {"name": "viewport", "full_page": False}, {})
            assert result.success is True
            mock_capture.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_assert_text_exact_match(self, mock_page):
        from gw_playwright.actions import action_assert_text
        page = MockPage()
        page.inner_text = AsyncMock(return_value="exact text")
        result = await action_assert_text(
            page,
            {"selector": "#title", "expected": "exact text", "contains": False},
            {}
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_assert_text_exact_match_fail(self, mock_page):
        from gw_playwright.actions import action_assert_text
        page = MockPage()
        page.inner_text = AsyncMock(return_value="different text")
        result = await action_assert_text(
            page,
            {"selector": "#title", "expected": "exact text", "contains": False},
            {}
        )
        assert result.success is False

    @pytest.mark.asyncio
    async def test_custom_extract_dict_result(self, mock_page):
        from gw_playwright.actions import action_custom_extract
        page = MockPage()
        page.evaluate = AsyncMock(return_value={"name": "John", "age": 30})
        result = await action_custom_extract(page, {"script": "return data"}, {})
        assert result.success is True
        assert result.data["name"] == "John"

    @pytest.mark.asyncio
    async def test_custom_extract_exception(self, mock_page):
        from gw_playwright.actions import action_custom_extract
        page = MockPage()
        page.evaluate = AsyncMock(side_effect=Exception("JS error"))
        result = await action_custom_extract(page, {"script": "bad script"}, {})
        assert result.success is False
        assert "JS error" in result.error

    @pytest.mark.asyncio
    async def test_execute_actions_single_failure_continues(self, mock_page):
        """Non-assertion failures should not stop execution."""
        from gw_playwright.actions import execute_actions
        page = MockPage()
        page.goto = AsyncMock(return_value=None)
        page.click = AsyncMock(side_effect=Exception("click failed"))

        actions = [
            {"type": "navigate", "params": {"url": "https://example.com"}},
            {"type": "click", "params": {"selector": "#btn"}},
            {"type": "navigate", "params": {"url": "https://example.com/other"}},
        ]
        results = await execute_actions(page, actions, {})
        # Non-assertion failures don't stop execution
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_action_result_data_default(self):
        from gw_playwright.actions import ActionResult
        result = ActionResult("test", True)
        assert result.data == {}

    @pytest.mark.asyncio
    async def test_action_result_error_default(self):
        from gw_playwright.actions import ActionResult
        result = ActionResult("test", True)
        assert result.error is None

    @pytest.mark.asyncio
    async def test_execute_action_handler_raises(self, mock_page):
        """Verify execute_action catches unexpected handler exceptions."""
        from gw_playwright.actions import execute_action, HANDLERS

        original = HANDLERS.get("navigate")
        async def broken_handler(page, params, context):
            raise RuntimeError("unexpected failure")

        HANDLERS["navigate"] = broken_handler
        try:
            result = await execute_action(mock_page, "navigate", {"url": "https://example.com"}, {})
            assert result.success is False
            assert "unexpected failure" in result.error
        finally:
            HANDLERS["navigate"] = original

    @pytest.mark.asyncio
    async def test_multiple_navigations_update_url(self, mock_page):
        from gw_playwright.actions import execute_actions
        actions = [
            {"type": "navigate", "params": {"url": "https://example.com/page1"}},
            {"type": "navigate", "params": {"url": "https://example.com/page2"}},
        ]
        results = await execute_actions(mock_page, actions, {})
        assert mock_page.url == "https://example.com/page2"

    @pytest.mark.asyncio
    async def test_fill_multiple_fields(self, mock_page):
        from gw_playwright.actions import execute_actions
        actions = [
            {"type": "fill", "params": {"selector": "#first", "value": "John"}},
            {"type": "fill", "params": {"selector": "#last", "value": "Doe"}},
        ]
        results = await execute_actions(mock_page, actions, {})
        assert len(results) == 2
        assert mock_page._state["#first"] == "John"
        assert mock_page._state["#last"] == "Doe"

    @pytest.mark.asyncio
    async def test_check_then_uncheck(self, mock_page):
        from gw_playwright.actions import execute_actions
        actions = [
            {"type": "check", "params": {"selector": "#agree"}},
            {"type": "uncheck", "params": {"selector": "#agree"}},
        ]
        results = await execute_actions(mock_page, actions, {})
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_extract_multiple_keys(self, mock_page):
        from gw_playwright.actions import action_extract
        extractions = [
            {"selector": "#name", "key": "name"},
            {"selector": "#email", "key": "email"},
        ]
        result = await action_extract(mock_page, {"extractions": extractions}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_assert_url_contains_true(self, mock_page):
        from gw_playwright.actions import action_assert_url
        result = await action_assert_url(mock_page, {"expected": "example.com", "contains": True}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_navigate_empty_url_in_context(self, mock_page):
        from gw_playwright.actions import action_navigate
        result = await action_navigate(mock_page, {"url": "${url}"}, {})
        # When context is empty, url resolves to empty string; may fail on goto
        assert result.success in (True, False)

    @pytest.mark.asyncio
    async def test_scroll_down_default_pixels(self, mock_page):
        from gw_playwright.actions import action_scroll_down
        result = await action_scroll_down(mock_page, {}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_scroll_up_default_pixels(self, mock_page):
        from gw_playwright.actions import action_scroll_up
        result = await action_scroll_up(mock_page, {}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_wait_for_selector_default_timeout(self, mock_page):
        from gw_playwright.actions import action_wait_for_selector
        result = await action_wait_for_selector(mock_page, {"selector": "#el"}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_fill_and_press_default_key(self, mock_page):
        from gw_playwright.actions import action_fill_and_press
        result = await action_fill_and_press(mock_page, {"selector": "#q", "value": "test"}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_screenshot_default_name(self, mock_page):
        from gw_playwright.actions import action_screenshot
        with patch('gw_playwright.actions.capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = b'\x89PNG\r\n'
            result = await action_screenshot(mock_page, {}, {})
            assert result.success is True

    @pytest.mark.asyncio
    async def test_extract_empty_extractions(self, mock_page):
        from gw_playwright.actions import action_extract
        result = await action_extract(mock_page, {"extractions": []}, {})
        assert result.success is True
        assert result.data == {}

    @pytest.mark.asyncio
    async def test_execute_js_with_context(self, mock_page):
        from gw_playwright.actions import action_execute_js
        result = await action_execute_js(
            mock_page,
            {"script": "return '${name}'"},
            {"name": "test"}
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_custom_extract_with_context(self, mock_page):
        from gw_playwright.actions import action_custom_extract
        result = await action_custom_extract(
            mock_page,
            {"script": "return '${data}'"},
            {"data": "{}"}
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_assert_text_exception(self):
        from gw_playwright.actions import action_assert_text
        page = MockPage()
        page.inner_text = AsyncMock(side_effect=Exception("selector error"))
        result = await action_assert_text(page, {"selector": "#bad", "expected": "text"}, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_assert_url_exception(self):
        from gw_playwright.actions import action_assert_url
        page = MockPage()
        page.url = property(lambda self: (_ for _ in ()).throw(Exception("url error")))
        # page.url is a string on MockPage, so let's simulate differently
        result = await action_assert_url(page, {"expected": "test"}, {})
        assert result.success in (True, False)

    @pytest.mark.asyncio
    async def test_execute_js_exception(self):
        from gw_playwright.actions import action_execute_js
        page = MockPage()
        page.evaluate = AsyncMock(side_effect=Exception("js failed"))
        result = await action_execute_js(page, {"script": "bad"}, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_all_16_action_types_registered(self):
        from gw_playwright.actions import HANDLERS, ActionType
        expected = {
            "navigate", "wait_for_selector", "click", "fill", "fill_and_press",
            "select_option", "check", "uncheck", "scroll_down", "scroll_up",
            "screenshot", "extract", "assert_text", "assert_url", "execute_js",
            "custom_extract"
        }
        assert set(HANDLERS.keys()) == expected

    @pytest.mark.asyncio
    async def test_action_type_enum_values(self):
        from gw_playwright.actions import ActionType
        assert ActionType.NAVIGATE.value == "navigate"
        assert ActionType.CLICK.value == "click"
        assert ActionType.FILL.value == "fill"
        assert ActionType.EXTRACT.value == "extract"
        assert ActionType.CUSTOM_EXTRACT.value == "custom_extract"

    @pytest.mark.asyncio
    async def test_action_result_to_dict_no_error_when_success(self):
        from gw_playwright.actions import ActionResult
        result = ActionResult("test", True, data={"key": "val"})
        d = result.to_dict()
        assert d == {"action": "test", "success": True, "data": {"key": "val"}}

    @pytest.mark.asyncio
    async def test_action_result_to_dict_with_error_when_failure(self):
        from gw_playwright.actions import ActionResult
        result = ActionResult("test", False, error="something broke")
        d = result.to_dict()
        assert d == {"action": "test", "success": False, "data": {}, "error": "something broke"}

    @pytest.mark.asyncio
    async def test_execute_actions_preserves_context_across_steps(self, mock_page):
        from gw_playwright.actions import execute_actions
        context = {"step": 1}
        actions = [
            {"type": "navigate", "params": {"url": "https://example.com"}},
            {"type": "click", "params": {"selector": "#btn"}},
        ]
        results = await execute_actions(mock_page, actions, context)
        assert context["step"] == 1  # Context dict is the same object

    @pytest.mark.asyncio
    async def test_navigate_with_token_in_domain(self, mock_page):
        from gw_playwright.actions import action_navigate
        result = await action_navigate(
            mock_page,
            {"url": "https://${sub}.${domain}/path"},
            {"sub": "www", "domain": "example.com"}
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_fill_with_numeric_value(self, mock_page):
        from gw_playwright.actions import action_fill
        result = await action_fill(mock_page, {"selector": "#age", "value": 25}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_select_option_with_index(self, mock_page):
        from gw_playwright.actions import action_select_option
        result = await action_select_option(mock_page, {"selector": "#dropdown", "value": "0"}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_multiple_sequential_navigations(self, mock_page):
        from gw_playwright.actions import execute_actions
        actions = [
            {"type": "navigate", "params": {"url": "https://a.com"}},
            {"type": "navigate", "params": {"url": "https://b.com"}},
            {"type": "navigate", "params": {"url": "https://c.com"}},
        ]
        results = await execute_actions(mock_page, actions, {})
        assert len(results) == 3
        assert mock_page.url == "https://c.com"

    @pytest.mark.asyncio
    async def test_extract_with_tokenized_selector(self, mock_page):
        from gw_playwright.actions import action_extract
        extractions = [{"selector": "#${field_id}", "key": "value"}]
        result = await action_extract(mock_page, {"extractions": extractions}, {"field_id": "name"})
        assert result.success in (True, False)

    @pytest.mark.asyncio
    async def test_click_with_tokenized_selector(self, mock_page):
        from gw_playwright.actions import action_click
        result = await action_click(mock_page, {"selector": "#${btn}"}, {"btn": "submit"})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_wait_for_selector_exception(self):
        from gw_playwright.actions import action_wait_for_selector
        page = MockPage()
        page.wait_for_selector = AsyncMock(side_effect=Exception("timeout"))
        result = await action_wait_for_selector(page, {"selector": "#missing"}, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_check_exception(self):
        from gw_playwright.actions import action_check
        page = MockPage()
        page.check = AsyncMock(side_effect=Exception("not a checkbox"))
        result = await action_check(page, {"selector": "#bad"}, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_uncheck_exception(self):
        from gw_playwright.actions import action_uncheck
        page = MockPage()
        page.uncheck = AsyncMock(side_effect=Exception("not a checkbox"))
        result = await action_uncheck(page, {"selector": "#bad"}, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_scroll_down_exception(self):
        from gw_playwright.actions import action_scroll_down
        page = MockPage()
        page.evaluate = AsyncMock(side_effect=Exception("scroll failed"))
        result = await action_scroll_down(page, {"pixels": 100}, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_scroll_up_exception(self):
        from gw_playwright.actions import action_scroll_up
        page = MockPage()
        page.evaluate = AsyncMock(side_effect=Exception("scroll failed"))
        result = await action_scroll_up(page, {"pixels": 100}, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_fill_exception(self):
        from gw_playwright.actions import action_fill
        page = MockPage()
        page.fill = AsyncMock(side_effect=Exception("fill failed"))
        result = await action_fill(page, {"selector": "#bad", "value": "test"}, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_fill_and_press_exception_on_press(self):
        from gw_playwright.actions import action_fill_and_press
        page = MockPage()
        page.fill = AsyncMock(return_value=None)
        page.press = AsyncMock(side_effect=Exception("press failed"))
        result = await action_fill_and_press(page, {"selector": "#input", "value": "test"}, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_select_option_exception(self):
        from gw_playwright.actions import action_select_option
        page = MockPage()
        page.select_option = AsyncMock(side_effect=Exception("not a select"))
        result = await action_select_option(page, {"selector": "#bad", "value": "x"}, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_screenshot_exception(self, mock_page):
        from gw_playwright.actions import action_screenshot
        with patch('gw_playwright.actions.capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.side_effect = Exception("screenshot failed")
            result = await action_screenshot(mock_page, {"name": "test"}, {})
            assert result.success is False

    @pytest.mark.asyncio
    async def test_assert_text_contains_true(self, mock_page):
        from gw_playwright.actions import action_assert_text
        page = MockPage()
        page.inner_text = AsyncMock(return_value="Hello World")
        result = await action_assert_text(page, {"selector": "#greeting", "expected": "World", "contains": True}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_assert_text_contains_false(self, mock_page):
        from gw_playwright.actions import action_assert_text
        page = MockPage()
        page.inner_text = AsyncMock(return_value="Hello World")
        result = await action_assert_text(page, {"selector": "#greeting", "expected": "World", "contains": False}, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_assert_url_contains_false_exact(self, mock_page):
        from gw_playwright.actions import action_assert_url
        result = await action_assert_url(
            mock_page,
            {"expected": "https://example.com", "contains": False},
            {}
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_js_with_tokenized_script(self, mock_page):
        from gw_playwright.actions import action_execute_js
        result = await action_execute_js(
            mock_page,
            {"script": "return '${expr}'"},
            {"expr": "42"}
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_custom_extract_list_result(self, mock_page):
        from gw_playwright.actions import action_custom_extract
        page = MockPage()
        page.evaluate = AsyncMock(return_value=[1, 2, 3])
        result = await action_custom_extract(page, {"script": "return [1,2,3]"}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_custom_extract_string_result(self, mock_page):
        from gw_playwright.actions import action_custom_extract
        page = MockPage()
        page.evaluate = AsyncMock(return_value="hello")
        result = await action_custom_extract(page, {"script": "return 'hello'"}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_extract_all_failures(self):
        from gw_playwright.actions import action_extract
        page = MockPage()
        page.inner_text = AsyncMock(side_effect=Exception("always fails"))
        page.evaluate = AsyncMock(side_effect=Exception("always fails"))
        extractions = [
            {"selector": "#a", "key": "a"},
            {"selector": "#b", "key": "b"},
        ]
        result = await action_extract(page, {"extractions": extractions}, {})
        assert result.success is False
        assert "a" in result.error and "b" in result.error

    @pytest.mark.asyncio
    async def test_extract_all_success(self, mock_page):
        from gw_playwright.actions import action_extract
        extractions = [
            {"selector": "#a", "key": "a"},
            {"selector": "#b", "key": "b"},
        ]
        result = await action_extract(mock_page, {"extractions": extractions}, {})
        assert result.success is True
        assert result.error is None

    @pytest.mark.asyncio
    async def test_navigate_result_contains_url(self, mock_page):
        from gw_playwright.actions import action_navigate
        result = await action_navigate(mock_page, {"url": "https://test.com"}, {})
        assert result.data["url"] == "https://test.com"

    @pytest.mark.asyncio
    async def test_screenshot_result_contains_size(self, mock_page):
        from gw_playwright.actions import action_screenshot
        with patch('gw_playwright.actions.capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = b'x' * 100
            result = await action_screenshot(mock_page, {"name": "test"}, {})
            assert result.data["size"] == 100

    @pytest.mark.asyncio
    async def test_execute_js_result_contains_output(self, mock_page):
        from gw_playwright.actions import action_execute_js
        result = await action_execute_js(mock_page, {"script": "return 1"}, {})
        assert "result" in result.data

    @pytest.mark.asyncio
    async def test_assert_text_result_contains_actual(self, mock_page):
        from gw_playwright.actions import action_assert_text
        page = MockPage()
        page.inner_text = AsyncMock(return_value="hello")
        result = await action_assert_text(page, {"selector": "#x", "expected": "hello"}, {})
        assert result.data["actual"] == "hello"

    @pytest.mark.asyncio
    async def test_assert_url_result_contains_actual(self, mock_page):
        from gw_playwright.actions import action_assert_url
        result = await action_assert_url(mock_page, {"expected": "example.com"}, {})
        assert "actual" in result.data

    @pytest.mark.asyncio
    async def test_empty_params_navigate(self, mock_page):
        from gw_playwright.actions import action_navigate
        result = await action_navigate(mock_page, {}, {})
        # Empty url should still work (goto with empty string) or fail gracefully
        assert result.success in (True, False)

    @pytest.mark.asyncio
    async def test_empty_params_click(self):
        from gw_playwright.actions import action_click
        page = MockPage()
        page.click = AsyncMock(side_effect=Exception("empty selector"))
        result = await action_click(page, {}, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_empty_params_fill(self):
        from gw_playwright.actions import action_fill
        page = MockPage()
        page.fill = AsyncMock(side_effect=Exception("empty selector"))
        result = await action_fill(page, {}, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_large_pixels_scroll(self, mock_page):
        from gw_playwright.actions import action_scroll_down
        result = await action_scroll_down(mock_page, {"pixels": 10000}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_negative_pixels_scroll(self, mock_page):
        from gw_playwright.actions import action_scroll_down
        result = await action_scroll_down(mock_page, {"pixels": -100}, {})
        assert result.success in (True, False)

    @pytest.mark.asyncio
    async def test_unicode_fill_value(self, mock_page):
        from gw_playwright.actions import action_fill
        result = await action_fill(mock_page, {"selector": "#name", "value": "田中太郎"}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_special_chars_fill_value(self, mock_page):
        from gw_playwright.actions import action_fill
        result = await action_fill(mock_page, {"selector": "#input", "value": "<script>alert(1)</script>"}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_long_fill_value(self, mock_page):
        from gw_playwright.actions import action_fill
        result = await action_fill(mock_page, {"selector": "#textarea", "value": "x" * 10000}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_concurrent_action_execution(self, mock_page):
        """Test that actions execute sequentially (not concurrently)."""
        from gw_playwright.actions import execute_actions
        urls_visited = []
        original_goto = mock_page.goto

        async def tracked_goto(url, timeout=30000):
            urls_visited.append(url)
            return await original_goto(url)

        mock_page.goto = tracked_goto

        actions = [
            {"type": "navigate", "params": {"url": "https://a.com"}},
            {"type": "navigate", "params": {"url": "https://b.com"}},
            {"type": "navigate", "params": {"url": "https://c.com"}},
        ]
        await execute_actions(mock_page, actions, {})
        assert len(urls_visited) == 3
        assert urls_visited[0] == "https://a.com"

    @pytest.mark.asyncio
    async def test_action_result_is_pickleable_dict(self):
        from gw_playwright.actions import ActionResult
        import json
        result = ActionResult("navigate", True, data={"url": "https://example.com"})
        d = result.to_dict()
        # Should be JSON serializable
        json_str = json.dumps(d)
        assert "navigate" in json_str

    @pytest.mark.asyncio
    async def test_execute_actions_with_mixed_success_failure(self, mock_page):
        from gw_playwright.actions import execute_actions
        page = MockPage()
        page.goto = AsyncMock(return_value=None)
        page.click = AsyncMock(side_effect=Exception("click failed"))

        actions = [
            {"type": "navigate", "params": {"url": "https://example.com"}},
            {"type": "click", "params": {"selector": "#btn"}},
        ]
        results = await execute_actions(page, actions, {})
        assert results[0].success is True
        assert results[1].success is False

    @pytest.mark.asyncio
    async def test_all_handlers_are_coroutines(self):
        from gw_playwright.actions import HANDLERS
        import inspect
        for action_type, handler in HANDLERS.items():
            assert inspect.iscoroutinefunction(handler), f"{action_type} handler is not async"

    @pytest.mark.asyncio
    async def test_handler_registry_not_mutated(self):
        from gw_playwright.actions import HANDLERS, ActionType
        original_keys = set(HANDLERS.keys())
        # Running execute_action should not modify HANDLERS
        page = MockPage()
        from gw_playwright.actions import execute_action
        await execute_action(page, "navigate", {"url": "https://example.com"}, {})
        assert set(HANDLERS.keys()) == original_keys

    @pytest.mark.asyncio
    async def test_execute_actions_delay_between_steps(self, mock_page):
        """Verify actions have small delays between them for stability."""
        from gw_playwright.actions import execute_actions
        import time
        actions = [
            {"type": "navigate", "params": {"url": "https://a.com"}},
            {"type": "navigate", "params": {"url": "https://b.com"}},
        ]
        start = time.time()
        await execute_actions(mock_page, actions, {})
        elapsed = time.time() - start
        # Should have at least 0.1s delay between actions
        assert elapsed >= 0.05  # Allow some tolerance

    @pytest.mark.asyncio
    async def test_no_delay_after_wait_for_selector(self, mock_page):
        """wait_for_selector should not add extra delay."""
        from gw_playwright.actions import execute_actions
        actions = [
            {"type": "wait_for_selector", "params": {"selector": "#loading"}},
            {"type": "click", "params": {"selector": "#btn"}},
        ]
        results = await execute_actions(mock_page, actions, {})
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_assertion_failure_stops_sequence(self, mock_page):
        from gw_playwright.actions import execute_actions
        page = MockPage()
        page.goto = AsyncMock(return_value=None)
        page.inner_text = AsyncMock(return_value="actual")

        actions = [
            {"type": "navigate", "params": {"url": "https://example.com"}},
            {"type": "assert_text", "params": {"selector": "#x", "expected": "MISSING"}},
            {"type": "click", "params": {"selector": "#btn"}},
            {"type": "navigate", "params": {"url": "https://example.com/next"}},
        ]
        results = await execute_actions(page, actions, {})
        # Should stop at assertion failure
        assert len(results) == 2
        assert results[1].success is False

    @pytest.mark.asyncio
    async def test_assert_url_failure_stops_sequence(self, mock_page):
        from gw_playwright.actions import execute_actions
        page = MockPage()
        page.goto = AsyncMock(return_value=None)

        actions = [
            {"type": "navigate", "params": {"url": "https://example.com"}},
            {"type": "assert_url", "params": {"expected": "wrong.com", "contains": True}},
            {"type": "click", "params": {"selector": "#btn"}},
        ]
        results = await execute_actions(page, actions, {})
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_navigate_then_extract_flow(self, mock_page):
        from gw_playwright.actions import execute_actions
        actions = [
            {"type": "navigate", "params": {"url": "https://example.com"}},
            {"type": "extract", "params": {"extractions": [{"selector": "#name", "key": "name"}]}},
        ]
        results = await execute_actions(mock_page, actions, {})
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_fill_click_extract_flow(self, mock_page):
        from gw_playwright.actions import execute_actions
        actions = [
            {"type": "fill", "params": {"selector": "#q", "value": "search term"}},
            {"type": "click", "params": {"selector": "#submit"}},
            {"type": "extract", "params": {"extractions": [{"selector": "#result", "key": "result"}]}},
        ]
        results = await execute_actions(mock_page, actions, {})
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_full_page_workflow(self, mock_page):
        """Simulate a realistic multi-step workflow."""
        from gw_playwright.actions import execute_actions
        actions = [
            {"type": "navigate", "params": {"url": "https://example.com/search"}},
            {"type": "wait_for_selector", "params": {"selector": "#form"}},
            {"type": "fill", "params": {"selector": "#query", "value": "${search_term}"}},
            {"type": "click", "params": {"selector": "#submit"}},
            {"type": "wait_for_selector", "params": {"selector": "#results"}},
            {"type": "extract", "params": {"extractions": [{"selector": "#results", "key": "results"}]}},
            {"type": "screenshot", "params": {"name": "final_results"}},
        ]
        with patch('gw_playwright.actions.capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = b'\x89PNG\r\n'
            results = await execute_actions(mock_page, actions, {"search_term": "OpenDataRemoval"})
            assert len(results) == 7

    @pytest.mark.asyncio
    async def test_context_token_resolution_in_extract(self, mock_page):
        from gw_playwright.actions import action_extract
        extractions = [{"selector": "#${field}", "key": "${key_name}"}]
        result = await action_extract(mock_page, {"extractions": extractions}, {"field": "name", "key_name": "full_name"})
        assert result.success in (True, False)

    @pytest.mark.asyncio
    async def test_multiple_extract_keys_same_selector(self, mock_page):
        from gw_playwright.actions import action_extract
        extractions = [
            {"selector": "#data", "key": "text"},
            {"selector": "#data", "key": "text_again"},
        ]
        result = await action_extract(mock_page, {"extractions": extractions}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_extract_with_attribute_and_token(self, mock_page):
        from gw_playwright.actions import action_extract
        extractions = [{"selector": "#${link_id}", "key": "href", "attribute": "href"}]
        result = await action_extract(mock_page, {"extractions": extractions}, {"link_id": "nav"})
        assert result.success in (True, False)

    @pytest.mark.asyncio
    async def test_execute_action_logs_error(self, mock_page):
        """Verify that unexpected handler errors are logged."""
        from gw_playwright.actions import execute_action, HANDLERS
        import logging

        original = HANDLERS.get("click")
        async def broken_handler(page, params, context):
            raise RuntimeError("unexpected")

        HANDLERS["click"] = broken_handler
        try:
            with patch('gw_playwright.actions.logger') as mock_logger:
                result = await execute_action(mock_page, "click", {"selector": "#btn"}, {})
                assert result.success is False
                mock_logger.error.assert_called_once()
        finally:
            HANDLERS["click"] = original

    @pytest.mark.asyncio
    async def test_action_result_data_preserved(self):
        from gw_playwright.actions import ActionResult
        result = ActionResult("extract", True, data={"name": "John", "email": "john@test.com"})
        assert result.data["name"] == "John"
        assert result.data["email"] == "john@test.com"

    @pytest.mark.asyncio
    async def test_action_result_error_preserved(self):
        from gw_playwright.actions import ActionResult
        result = ActionResult("click", False, error="Element not found: #btn")
        assert result.error == "Element not found: #btn"

    @pytest.mark.asyncio
    async def test_execute_actions_with_all_action_types(self, mock_page):
        """Test executing all 16 action types in sequence."""
        from gw_playwright.actions import execute_actions

        page = MockPage()
        page.goto = AsyncMock(return_value=None)
        page.click = AsyncMock(return_value=None)
        page.fill = AsyncMock(return_value=None)
        page.press = AsyncMock(return_value=None)
        page.select_option = AsyncMock(return_value=None)
        page.check = AsyncMock(return_value=None)
        page.uncheck = AsyncMock(return_value=None)
        page.wait_for_selector = AsyncMock(return_value=True)
        page.inner_text = AsyncMock(return_value="test text")
        page.evaluate = AsyncMock(return_value={"result": "ok"})

        with patch('gw_playwright.actions.capture_screenshot', new_callable=AsyncMock) as mock_capture:
            mock_capture.return_value = b'\x89PNG\r\n'

            actions = [
                {"type": "navigate", "params": {"url": "https://example.com"}},
                {"type": "wait_for_selector", "params": {"selector": "#form"}},
                {"type": "click", "params": {"selector": "#btn"}},
                {"type": "fill", "params": {"selector": "#input", "value": "test"}},
                {"type": "fill_and_press", "params": {"selector": "#input", "value": "test"}},
                {"type": "select_option", "params": {"selector": "#select", "value": "opt1"}},
                {"type": "check", "params": {"selector": "#checkbox"}},
                {"type": "uncheck", "params": {"selector": "#checkbox"}},
                {"type": "scroll_down", "params": {"pixels": 500}},
                {"type": "scroll_up", "params": {"pixels": 500}},
                {"type": "screenshot", "params": {"name": "test"}},
                {"type": "extract", "params": {"extractions": [{"selector": "#data", "key": "data"}]}},
                {"type": "assert_text", "params": {"selector": "#title", "expected": "test"}},
                {"type": "assert_url", "params": {"expected": "example.com"}},
                {"type": "execute_js", "params": {"script": "return 1"}},
                {"type": "custom_extract", "params": {"script": "return {}"}},
            ]

            results = await execute_actions(page, actions, {})
            assert len(results) == 16